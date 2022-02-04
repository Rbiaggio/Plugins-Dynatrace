import logging
import tempfile
from hashlib import sha256
import json
from pathlib import Path
from typing import List, Generator, Union
import os


current_file_path = os.path.dirname(os.path.realpath(__file__))
cache_file = os.path.join(current_file_path, "citrixagent", "config", "log_cache.json")

log = logging.getLogger(__name__)


def _hash(line: str):
    return sha256(line.encode()).hexdigest()


def _tail(file_name: Union[Path, str], num_lines: int):
    # Very naive implementation, I know the files are less than 10MB
    try:
        with open(file_name, "r") as f:
            return [line.strip() for line in f.readlines()[-num_lines:]]
    except Exception as e:
        log.error(f"Could not process file {file_name}: {e}")
        return []


class LogProxy:
    def __init__(self, log_path: Path, cache_location: Path = None):
        self.cache_location = cache_location
        if self.cache_location is None:
            self.cache_location = Path(f"{tempfile.gettempdir()}/log_proxy.json")

        self.log_path = log_path

    def _get_cache(self) -> List[str]:
        try:
            with open(self.cache_location, "r") as f:
                return json.load(f)
        except Exception as e:
            log.warning(f"Could not read the log cache records from {self.cache_location}: {e}")
            return []

    def _update_cache(self, lines: List[str]):
        try:
            with open(self.cache_location, "w") as f:
                json.dump(lines, f)
        except Exception as e:
            log.warning(f"Could not insert log cache records to {self.cache_location}: {e}")

    def get_lines_from_file(self, num_lines=1000) -> Generator[str, None, None]:
        current_lines_hash = []
        previous_lines_hash = self._get_cache()
        for line in _tail(self.log_path, num_lines):
            hash_line = _hash(line)
            if hash_line not in previous_lines_hash:
                yield line
            current_lines_hash.append(hash_line)
        self._update_cache(current_lines_hash)
