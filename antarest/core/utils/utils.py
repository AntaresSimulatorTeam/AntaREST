import time
from glob import escape
from pathlib import Path
from typing import IO, Any, Optional, Callable
from zipfile import ZipFile, BadZipFile

import redis

from antarest.core.config import RedisConfig
from antarest.core.exceptions import BadZipBinary


class DTO:
    """
    Implement basic method for DTO objects
    """

    def __hash__(self) -> int:
        return hash(tuple(sorted(self.__dict__.items())))

    def __eq__(self, other: Any) -> bool:
        return (
            isinstance(other, type(self)) and self.__dict__ == other.__dict__
        )

    def __str__(self) -> str:
        return "{}({})".format(
            type(self).__name__,
            ", ".join(
                [
                    "{}={}".format(k, str(self.__dict__[k]))
                    for k in sorted(self.__dict__)
                ]
            ),
        )

    def __repr__(self) -> str:
        return self.__str__()


def sanitize_uuid(uuid: str) -> str:
    return str(escape(uuid))


def extract_zip(stream: IO[bytes], dst: Path) -> None:
    """
    Extract zip archive
    Args:
        stream: zip file
        dst: destination path

    Returns:

    """
    try:
        with ZipFile(stream) as zip_output:
            zip_output.extractall(path=dst)
    except BadZipFile:
        raise BadZipBinary("Only zip file are allowed.")


def get_default_config_path() -> Optional[Path]:
    config = Path("config.yaml")
    if config.exists():
        return config

    config = Path.home() / ".antares/config.yaml"
    if config.exists():
        return config
    return None


def get_local_path() -> Path:
    # https: // pyinstaller.readthedocs.io / en / stable / runtime - information.html
    filepath = Path(__file__).parent.parent.parent.parent
    return filepath


def new_redis_instance(config: RedisConfig) -> redis.Redis:
    return redis.Redis(host=config.host, port=config.port, db=0)


class StopWatch:
    def __init__(self) -> None:
        self.current_time: float = time.time()
        self.start_time = self.current_time

    def reset_current(self) -> None:
        self.current_time = time.time()

    def log_elapsed(
        self, logger: Callable[[float], None], since_start: bool = False
    ) -> None:
        logger(
            time.time() - self.start_time if since_start else self.current_time
        )
        self.current_time = time.time()
