import os
import logging
from pathlib import Path

from .process_controller import start_process

default_logger = logging.getLogger(__name__)

current_file_path = os.path.dirname(os.path.realpath(__file__))


def find_java_bin():
    locations = [
        f"../../../../gateway/jre/bin/java{'.exe' if os.name == 'nt' else ''}",
        "/opt/dynatrace/gateway/jre/bin/java",
        "C:/Program Files/dynatrace/gateway/jre/bin/java.exe",
        "D:/Program Files/dynatrace/gateway/jre/bin/java.exe",
    ]

    for location in locations:
        if Path(location).exists():
            return location

    if os.environ.get("GATEWAY_HOME", False):
        return f"{os.environ.get('GATEWAY_HOME')}/jre/bin/java"

    return "java"


def query(endpoint_id: int, temp_folder: Path) -> None:
    cmd_args = [
        "-cp",
        os.path.join(current_file_path, "../jars/*"),
        "com.dynatrace.jdbc.connector.Main",
        "-endpoint",
        f"{endpoint_id}",
        "-tempfolder",
        f"{temp_folder}",
    ]
    cmd = [find_java_bin(), *cmd_args]
    start_process(cmd)
