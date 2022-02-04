import logging
from typing import List, Optional, Dict

default_logger = logging.getLogger(__name__)


class MintMetric:
    def __init__(
        self,
        key: str,
        value: Optional[float] = None,
        dimensions: Dict[str, str] = None,
        gauge_min: Optional[float] = None,
        gauge_max: Optional[float] = None,
        gauge_sum: Optional[float] = None,
        gauge_count: Optional[float] = None,
        timestamp: Optional[int] = None,
    ):
        self.key = key
        self.value = value
        self.gauge_min = gauge_min
        self.gauge_max = gauge_max
        self.gauge_sum = gauge_sum
        self.gauge_count = gauge_count
        if dimensions is None:
            dimensions = {}
        self.dimensions = dimensions
        self.timestamp = timestamp

    def __hash__(self):
        return hash(self.key_and_dimension())

    def __eq__(self, other):
        return self.key_and_dimension() == other.key_and_dimension()

    def key_and_dimension(self):
        dimensions_string = ",".join([f'{k}="{v}"' for k, v in self.dimensions.items()])
        return f"{self.key},{dimensions_string}"

    def to_mint(self):
        value = self.value
        if self.gauge_min is not None:
            value = f"gauge,min={self.gauge_min}"
        if self.gauge_max is not None:
            value = f"{value},max={self.gauge_max}"
        if self.gauge_sum is not None:
            value = f"{value},sum={self.gauge_sum}"
        if self.gauge_count is not None:
            value = f"{value},count={self.gauge_count}"

        if self.timestamp is not None:
            value = f"{value} {self.timestamp}"

        return f"{self.key_and_dimension()} {value}"

    def __repr__(self):
        return self.to_mint()


class QueryConfig:
    def __init__(
        self, name: str, query: str, value_columns: List[str], dimension_columns: List[str], will_run_now: bool = False, extra_dimensions: Optional[str] = None
    ):
        super().__init__()
        self.name: str = name
        self.query: str = query
        self.value_columns: List[str] = value_columns
        self.dimension_columns: List[str] = dimension_columns
        self.will_run_now = will_run_now
        self.extra_dimensions = extra_dimensions

    def __repr__(self):
        return f"Query(name: {self.name}, value_columns:{self.value_columns}, dimension_columns:{self.dimension_columns}, extra_dimensions={self.extra_dimensions})"


class Column(object):
    def __init__(self, col_json: dict):
        self.name = col_json["name"]
        self.value = col_json["value"]
        self.index = col_json["index"]

    def __str__(self):
        return f"{self.name}: {self.value}"

    def __repr__(self):
        return f"Column(Index:{self.index},: Name={self.name}, Value={self.value})"


class Row(object):
    def __init__(self, columns: List[Column]):
        self.columns = sorted(columns, key=lambda col: col.index)

    def __repr__(self):
        return f"Row(columns={self.columns})"

    def get_column_by_index(self, index) -> Column:
        for c in self.columns:
            if c.index == index:
                return c
        raise Exception(f"Index {index} is out of range ({len(self.columns)} columns present)")

    def get_column_by_name(self, name: str) -> Column:
        for c in self.columns:
            if str(c.name).upper() == name.upper():
                return c
        raise Exception(f"Could not find column with name: '{name}'. Only had: {[c.name for c in self.columns]}")


class Result(object):
    def __init__(self, logger=default_logger):
        self.error: bool = False
        self.error_message: Optional[str] = None
        self.rows: List[Row] = []
        self.logger = logger
        self.name = ""
        self.duration: int = 0
        self.timestamp: int = 0

    @staticmethod
    def from_json(json_dict: dict) -> "Result":
        r = Result()
        if json_dict is not None:
            try:
                r.error = json_dict["error"]
                r.error_message = json_dict.get("errorMessage", "")
                r.duration = json_dict.get("duration", 0)
                r.timestamp = json_dict.get("timestamp", 0)
                r.name = json_dict.get("name", 0)

                if not r.error:
                    for row in json_dict.get("rows", []):
                        r.rows.append(Row([Column(col) for col in row["columns"]]))
            except Exception as e:
                error = f"Could not parse result: {e}. The result was: '{json_dict}'"
                r.error = True
                r.error_message = error
                r.logger.exception(error)

        return r

    def __repr__(self):
        return f"Result(name='{self.name}', error={self.error}, error_message='{self.error_message}', rows={len(self.rows)})"

    def __str__(self):
        return self.__repr__()
