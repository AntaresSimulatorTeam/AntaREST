import os
import shutil
import time
from glob import escape
from pathlib import Path
from typing import IO, Any, Optional, Callable, TypeVar, List, Union, Awaitable
from zipfile import (
    ZipFile,
    BadZipFile,
    ZIP_STORED,
    ZIP_DEFLATED,
    ZIP_BZIP2,
    ZIP_LZMA,
)

import redis

from antarest.core.config import RedisConfig
from antarest.core.exceptions import BadZipBinary, ShouldNotHappenException


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

    config = Path("../config.yaml")
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


def new_redis_instance(config: RedisConfig) -> redis.Redis:  # type: ignore
    redis_client = redis.Redis(
        host=config.host, port=config.port, password=config.password, db=0
    )
    return redis_client


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
            time.time()
            - (self.start_time if since_start else self.current_time)
        )
        self.current_time = time.time()


T = TypeVar("T")


def retry(
    func: Callable[[], T], attempts: int = 10, interval: float = 0.5
) -> T:
    attempt = 0
    catched_exception: Optional[Exception] = None
    while attempt < attempts:
        try:
            attempt += 1
            return func()
        except Exception as e:
            time.sleep(interval)
            catched_exception = e
    raise catched_exception or ShouldNotHappenException()


def assert_this(b: Any) -> None:
    if not b:
        raise AssertionError


def concat_files(files: List[Path], target: Path) -> None:
    with open(target, "w") as fh:
        for item in files:
            with open(item, "r") as infile:
                for line in infile:
                    fh.write(line)


def zip_dir(
    dir_path: Path, zip_path: Path, remove_source_dir: bool = False
) -> None:
    with ZipFile(
        zip_path, mode="w", compression=ZIP_DEFLATED, compresslevel=2
    ) as zipf:
        len_dir_path = len(str(dir_path))
        for root, _, files in os.walk(dir_path):
            for file in files:
                file_path = os.path.join(root, file)
                zipf.write(file_path, file_path[len_dir_path:])
    if remove_source_dir:
        shutil.rmtree(dir_path)


def unzip(
    dir_path: Path, zip_path: Path, remove_source_zip: bool = False
) -> None:
    with ZipFile(zip_path, mode="r") as zipf:
        zipf.extractall(dir_path)
    if remove_source_zip:
        zip_path.unlink()


def suppress_exception(
    callback: Callable[[], T],
    logger: Callable[[Exception], None],
) -> Optional[T]:
    try:
        return callback()
    except Exception as e:
        logger(e)
        return None
