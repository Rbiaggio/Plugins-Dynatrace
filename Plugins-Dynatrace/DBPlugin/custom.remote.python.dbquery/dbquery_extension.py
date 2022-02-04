import os
import json
import base64
import tempfile
from datetime import timedelta, datetime
from pathlib import Path
import time
from typing import Dict, List
import unicodedata
import re

from croniter import croniter
from ruxit.api.base_plugin import RemoteBasePlugin
from ruxit.api.exceptions import NothingToReportException

from dbquery_imports.log_proxy import LogProxy
from dbquery_imports.models import Result, QueryConfig, MintMetric
from dbquery_imports import connector
from dynatrace import Dynatrace


def chunks(elements, size):
    for i in range(0, len(elements), size):
        yield elements[i : i + size]


class CustomDBQueryPluginRemote(RemoteBasePlugin):
    def initialize(self, **kwargs):
        self.not_sent_yet: Dict[str, QueryConfig] = {}
        self.temp_folder = create_or_get_temp_folder()

    def query(self, **kwargs):
        start_time = time.time()

        self.logger.setLevel(self.config.get("log_level"))

        # This determines if we always send metrics every minute, even when queries are not running every minute
        self.send_cached = self.config.get("send_cached", True)

        group_name = self.config.get("group_name") or "Custom DB Queries Group"
        device_name = self.config.get("custom_device_name") or "Custom DB Queries Device"
        group = self.topology_builder.create_group(group_name, group_name)
        self.custom_device = group.create_device(device_name)
        self.custom_device_id = f"CUSTOM_DEVICE-{self.custom_device.id:X}"

        dt = Dynatrace(self.config["dt_api_url"], self.config["dt_api_token"], log=self.logger)

        # This is for us to send statistics about the queries, like response time, status, number of rows, for troubleshooting purposes
        self.send_statistics = self.config.get("send_statistics", False)
        statistics_group = self.topology_builder.create_group("DBQuery Monitoring", "DBQuery Monitoring")
        name = self.activation.entity_id
        if self.activation.endpoint_name:
            name = self.activation.endpoint_name
        self.statistics_device = statistics_group.create_device(f"Statistics ({self.activation.entity_id})", f"DB Query Statistics ({name})")

        if self.send_statistics:
            self.statistics_device.report_property("Endpoint name or ID", f"{name}")
            self.statistics_device.report_property("Type", self.config.get("database_type"))
            self.statistics_device.report_property("Host", self.config.get("database_host"))

        # First, figure out which queries to run, based on the schedules
        queries = self.get_queries()
        queries_to_run = [q for q in queries if q.will_run_now]

        if self.send_statistics:
            self.statistics_device.report_property("Queries", f"{len(queries)}")
        if queries_to_run:
            # Write the config only for the queries that must run now, and start the java process that does the querying
            self.write_config(queries_to_run)
            connector.query(self.activation.entity_id, self.temp_folder)

        # Collect the queries results, send them 1000 MINT lines at a time
        mint_lines = self.parse_results(queries)
        for lines_subset in chunks(mint_lines, 1000):
            try:
                mint_strings = [m.to_mint() for m in lines_subset]
                self.logger.info(f"Reporting lines: {mint_strings}")
                dt.metrics.ingest(mint_strings)
            except Exception as e:
                self.logger.error(f"Could not publish all metrics: {e}")

        self.parse_logs()

        self.custom_device.absolute("duration", time.time() - start_time)

    def parse_logs(self):
        log = Path(self.temp_folder, "log", f"{self.activation.entity_id}.log")
        cache = Path(self.temp_folder, f"{self.activation.entity_id}.json")

        for line in LogProxy(log, cache).get_lines_from_file():
            self.logger.info(line)
            if "level=error" in line or "level=warn" in line or "level=fatal" in line:
                self.statistics_device.report_custom_info_event(f"Received a bad line from the log: {line}", "Bad log line received", properties={"line": line})

    def get_queries(self) -> List[QueryConfig]:
        """
        Determines which queries need to be run on this interval
        This is based on the schedule of the query, by default a query runs every minute
        :return: Two lists of QueryConfig, the first one are the queries to run, and the second
        the queries not to run
        """
        queries = []
        now = datetime.now().astimezone()

        # We have up to 10 queries
        for i in range(1, 11):
            name = self.config.get(f"query_{i}_name", "")

            try:
                if name != "":  # Queries that don't have a name are ignored
                    schedule = self.config.get(f"query_{i}_schedule") or "*/1 * * * *"  # Default schedule is every minute
                    query_string = self.config[f"query_{i}_value"]
                    value_columns_raw = self.config.get(f"query_{i}_value_columns", "")
                    dimension_columns_raw = self.config.get(f"query_{i}_dimension_columns", "")
                    extra_dimensions = self.config.get(f"query_{i}_extra_dimensions", "")
                    value_columns = []
                    dimension_columns = []
                    if value_columns_raw:
                        value_columns = value_columns_raw.split(",")
                    if dimension_columns_raw:
                        dimension_columns = dimension_columns_raw.split(",")

                    cron = croniter(schedule, now, ret_type=datetime)
                    previous_execution = cron.get_prev().astimezone()
                    next_execution = cron.get_next().astimezone()

                    query_config = QueryConfig(name, query_string, value_columns, dimension_columns, extra_dimensions=extra_dimensions)

                    time_since = now - previous_execution
                    if time_since <= timedelta(minutes=1):
                        self.logger.info(f"Adding query '{name}' because it has been scheduled to run {time_since} ago ({previous_execution}) ")
                        query_config.will_run_now = True
                    else:
                        self.logger.info(f"Not adding query '{name}'. Next execution at {next_execution}, now is {now}")
                        query_config.will_run_now = False
                    queries.append(query_config)
                    if self.send_statistics:
                        state = "RUNNING" if query_config.will_run_now else "CACHED"
                        self.statistics_device.state_metric("query_state", state, dimensions={"Query": query_config.name})

            except Exception as e:
                self.logger.error(f"Could not add query {name}, error: {e}")

        return queries

    def write_config(self, queries_to_run: List[QueryConfig]):
        """
        Writes the database configuration to a json file named after the endpoint ID
        """

        driver_classes = {
            "DB2": "com.ibm.db2.jcc.DB2Driver",
            "SQL Server": "com.microsoft.sqlserver.jdbc.SQLServerDriver",
            "Oracle": "oracle.jdbc.driver.OracleDriver",
            "MySQL": "com.mysql.cj.jdbc.Driver",
        }

        queries_json = [query.__dict__ for query in queries_to_run]
        config = {
            "host": self.config["database_host"],
            "port": self.config["database_port"],
            "username": self.config["database_username"],
            "password": encode(self.config["database_password"]),
            "logLevel": self.config["log_level"],
            "queries": queries_json,
            "driverClassName": driver_classes.get(self.config["database_type"]),
            "connectionString": self.config.get("jdbc_connection_string", ""),
            "oracleListenerType": self.config.get("oracle_listener_type", ""),
            "database": self.config["database_name"],
        }

        path = Path(self.temp_folder)
        if not path.exists():
            os.mkdir(path)
        path = Path(self.temp_folder, "config")
        if not path.exists():
            os.mkdir(path)
        with open(Path(path, f"{self.activation.entity_id}.json"), "w") as f:
            json.dump(config, f, indent=2)

    def parse_results(self, queries: List[QueryConfig]) -> List[MintMetric]:
        """
        Parses the results of the queries and returns a list of the results.

        The results are stored as a json file in the temp folder.
        There is one file per endpoint ID
        """
        mint_lines = []
        now = datetime.now().astimezone()

        results = self.read_results_from_file()
        for query in queries:
            result = results.get(query.name)

            # The result file doesn't even exist yet, the query did not have time to run once
            if result is None:
                self.logger.warning(f"Needed to send query {query} but the result is not available yet")
                self.not_sent_yet[query.name] = query
                continue

            # The result file exists, but how long ago was the query executed?
            query_timestamp = datetime.fromtimestamp(result.timestamp).astimezone()
            difference_from_now = now - query_timestamp
            self.logger.debug(
                f"Processing '{query.name}', we are at {now}, the query response was written at {query_timestamp}, the difference is {difference_from_now}"
            )

            # In this case, the query ran more than one minute ago, but the user wants us to send this cached result
            if self.send_cached and difference_from_now > timedelta(minutes=1) and query.name not in self.not_sent_yet:
                self.logger.info(f"Sending cached value for '{query.name}'")
                mint_lines.extend(self.parse_result(query, result))
                continue

            # In this case, this result is too old, but the user does not want to send cached results
            # we need to keep this query in self.not_sent_yet because we are waiting for a more recent result
            elif not self.send_cached and difference_from_now > timedelta(minutes=2):
                self.logger.info(f"Adding '{query.name} to not_sent_yet because the results are too old: {difference_from_now} ago")
                self.not_sent_yet[query.name] = query
                continue

            # When we get here, this is either a query that was supposed to run now and it did
            # Or a query that is in self.not_sent_yet and ran now, we were waiting for this result
            mint_lines.extend(self.parse_result(query, result))
            if query.name in self.not_sent_yet:
                del self.not_sent_yet[query.name]

        return mint_lines

    def parse_result(self, query: QueryConfig, result: Result) -> List[MintMetric]:
        self.logger.info(f"Query: {query}, Result: {result}")
        mint_lines: List[MintMetric] = []
        if result.error:
            title = f"Error during query execution for {query.name}"
            description = f"There was an error obtaining the results. The error was: {result.error_message}"
            self.statistics_device.report_error_event(description, title, properties={"Query": result.name})
            if self.send_statistics:
                self.statistics_device.state_metric("query_state", "ERROR", dimensions={"Query": result.name})

        if self.send_statistics:
            self.statistics_device.absolute("query_duration", result.duration, dimensions={"Query": result.name})
            self.statistics_device.absolute("query_rows", len(result.rows), dimensions={"Query": result.name})

        # These are optional hardcoded dimensions from plugin.json
        extra_dimensions: Dict[str, str] = {k: v for k, v in query.extra_dimensions.split(",")} if query.extra_dimensions else {}
        extra_dimensions["dt.entity.custom_device"] = self.custom_device_id
        extra_dimensions["query_name"] = query.name

        metric_name = "custom.db.query"
        for row in result.rows:
            try:
                dimensions: Dict[str, str] = extra_dimensions.copy()
                if query.value_columns:
                    # If the user chose which columns to get
                    for c in query.dimension_columns:
                        # If the user chose to get dimension columns
                        col = row.get_column_by_name(c)
                        dimensions[slugify(col.name)] = col.value

                    for column in query.value_columns:
                        # Report dimensions and values
                        col = row.get_column_by_name(column)
                        if dimensions:
                            report_dimensions = dimensions.copy()
                            report_dimensions["column"] = slugify(column)
                            self.logger.debug(f"{query.name} - Reporting dimensions: {report_dimensions}, value: {col.value}")
                            mint_lines.append(MintMetric(metric_name, col.value, report_dimensions))
                        else:
                            self.logger.debug(f"{query.name} - Reporting value for column {column} (no dimension): {col}")
                            mint_lines.append(MintMetric(metric_name, col.value, {"column": column}))
                else:
                    # If no columns were selected, report the first column of the first row
                    col = row.columns[0]
                    self.logger.debug(f"{query.name} - No columns set, reporting first column of the first row: {col}")
                    if dimensions:
                        mint_lines.append(MintMetric(metric_name, col.value, dimensions))
                    else:
                        mint_lines.append(MintMetric(metric_name, col.value))

                    break  # We ignore the rest of the rows in this case
            except Exception as e:
                self.logger.exception(f"{query.name} - Could not parse rows: {e}")

        return mint_lines

    def read_results_from_file(self) -> Dict[str, Result]:
        results = {}
        path = Path(self.temp_folder, "results")
        results_file = Path(path, f"{self.activation.entity_id}.json")
        if os.path.exists(results_file):
            with open(results_file, "r") as f:
                try:
                    json_value = json.load(f)
                    if json_value["error"]:
                        self.logger.error(f"There was an error returned from the connector {results_file}: {json_value['errorMessage']}")
                        json_value["queries"] = []
                        if self.send_statistics:
                            self.statistics_device.state_metric("result_state", "ERROR")
                    else:
                        self.statistics_device.state_metric("result_state", "RUNNING")
                    for query in json_value.get("queries", []):
                        result = Result.from_json(query)
                        results[result.name] = result
                except Exception as e:
                    self.logger.error(f"Could not parse json from {results_file}: {e}")
                    raise NothingToReportException(f"Error: {e}")

        return results


def encode(value: str) -> str:
    return base64.b64encode(value.encode("utf-8")).decode()


def slugify(value: str) -> str:
    value = unicodedata.normalize("NFKC", value)
    value = re.sub(r"[:.-/\s]+", "_", value)
    value = re.sub(r"[^\w\s-]", "", value)
    return value.lower()


def create_or_get_temp_folder():
    temp_folder = Path(tempfile.gettempdir(), "dynatrace-ag-dbquery")
    if not temp_folder.exists():
        os.mkdir(temp_folder)
    return temp_folder
