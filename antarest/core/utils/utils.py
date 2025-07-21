# Copyright (c) 2025, RTE (https://www.rte-france.com)
#
# See AUTHORS.txt
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# SPDX-License-Identifier: MPL-2.0
#
# This file is part of the Antares project.

import base64
import glob
import http
import logging
import re
import time
from pathlib import Path
from typing import Any, Callable, List, Optional, TypeVar

from fastapi import HTTPException
from typing_extensions import override

from antarest.core.exceptions import ShouldNotHappenException

logger = logging.getLogger(__name__)

UUID_PATTERN = re.compile("^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")


class DTO:
    """
    Implement basic method for DTO objects
    """

    @override
    def __hash__(self) -> int:
        return hash(tuple(sorted(self.__dict__.items())))

    @override
    def __eq__(self, other: Any) -> bool:
        return isinstance(other, type(self)) and self.__dict__ == other.__dict__

    @override
    def __str__(self) -> str:
        return "{}({})".format(
            type(self).__name__,
            ", ".join(["{}={}".format(k, str(self.__dict__[k])) for k in sorted(self.__dict__)]),
        )

    @override
    def __repr__(self) -> str:
        return self.__str__()


def sanitize_uuid(uuid: str) -> str:
    if not UUID_PATTERN.match(uuid):
        sanitized_id = base64.b64encode(uuid.encode("utf-8")).decode("utf-8")
        raise HTTPException(status_code=http.HTTPStatus.BAD_REQUEST, detail=f"uuid {sanitized_id} is not a valid UUID")
    return uuid


def validate_study_name(name: str) -> str:
    """
    Validates study name by rejecting '=' and '/' characters.

    These characters are forbidden as they conflict with URL parameters
    and file system paths.
    """
    if any(char in name for char in ["=", "/"]):
        raise HTTPException(
            status_code=http.HTTPStatus.BAD_REQUEST, detail=f"study name {name} contains illegal characters (=, /)"
        )
    return name.strip()


def validate_folder_path(path: str) -> str:
    """
    Validates folder path by rejecting '=' character and removing trailing '/'.

    The '=' character is forbidden as it conflicts with URL parameters.
    """
    if "=" in path:
        raise HTTPException(
            status_code=http.HTTPStatus.BAD_REQUEST, detail=f"folder name {path} contains illegal character '='"
        )
    path = path.rstrip("/")
    return path.strip()


def sanitize_string(string: str) -> str:
    return str(glob.escape(string))


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


class StopWatch:
    def __init__(self) -> None:
        self.current_time: float = time.time()
        self.start_time = self.current_time

    def reset_current(self) -> None:
        self.current_time = time.time()

    def log_elapsed(self, logger_: Callable[[float], None], since_start: bool = False) -> None:
        logger_(time.time() - (self.start_time if since_start else self.current_time))
        self.current_time = time.time()


T = TypeVar("T")


def retry(func: Callable[[], T], attempts: int = 10, interval: float = 0.5) -> T:
    attempt = 0
    caught_exception: Optional[Exception] = None
    while attempt < attempts:
        try:
            attempt += 1
            return func()
        except Exception as e:
            logger.info(f"💤 Sleeping {interval} second(s) before retry...", exc_info=e)
            time.sleep(interval)
            caught_exception = e
    raise caught_exception or ShouldNotHappenException()


def assert_this(b: Any) -> None:
    if not b:
        raise AssertionError


def concat_files(files: List[Path], target: Path) -> None:
    with open(target, "w") as fh:
        for item in files:
            with open(item, "r") as infile:
                for line in infile:
                    fh.write(line)


def concat_files_to_str(files: List[Path]) -> str:
    concat_str = ""
    for item in files:
        with open(item, "r") as infile:
            for line in infile:
                concat_str += line
    return concat_str


def suppress_exception(
    callback: Callable[[], T],
    logger_: Callable[[Exception], None],
) -> Optional[T]:
    try:
        return callback()
    except Exception as e:
        logger_(e)
        return None
