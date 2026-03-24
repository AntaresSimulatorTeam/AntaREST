# Copyright (c) 2026, RTE (https://www.rte-france.com)
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

import datetime
import glob
import http
import logging
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any, TypeVar

from fastapi import HTTPException
from typing_extensions import override

from antarest.core.exceptions import ShouldNotHappenException

logger = logging.getLogger(__name__)


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
            ", ".join([f"{k}={str(self.__dict__[k])}" for k in sorted(self.__dict__)]),
        )

    @override
    def __repr__(self) -> str:
        return self.__str__()


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


def get_default_config_path() -> Path | None:
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
    """A simple stopwatch for measuring elapsed time, with support for laps.

    The stopwatch starts automatically on creation. It tracks two timers:
    a start timer (never reset) and a lap timer (reset on each call to ``lap()``).

    Properties:
        since_start: Total time since creation (never resets).
        elapsed: Time since the last ``lap()`` call (or creation if ``lap()`` was never called).

    Methods:
        lap(): Returns the time since the last lap and resets the lap timer.

    The stopwatch can also be used directly in f-strings via ``__format__``,
    which formats the time since the last lap.

    Examples::

        stopwatch = StopWatch()

        do_first_step()
        logger.info(f"First step done in {stopwatch.lap()}s")

        do_second_step()
        logger.info(f"Second step done in {stopwatch.lap()}s")

        logger.info(f"Total time: {stopwatch.since_start}s")

        # Using __format__ for the current lap duration without resetting:
        do_third_step()
        logger.info(f"Third step running for {stopwatch:.2f}s")
    """

    def __init__(self) -> None:
        self._start: float = time.time()
        self._lap: float = self._start

    def lap(self) -> float:
        """Return the time elapsed since the last lap (or creation), then reset the lap timer."""
        now = time.time()
        elapsed = now - self._lap
        self._lap = now
        return elapsed

    @property
    def since_start(self) -> float:
        """Return the time elapsed since creation. No side effects."""
        return time.time() - self._start

    @property
    def elapsed(self) -> float:
        """Return the time elapsed since the last lap (or creation). No side effects."""
        return time.time() - self._lap

    @override
    def __format__(self, format_spec: str) -> str:
        """Format the time elapsed since the last lap. No side effects (does not reset the lap timer)."""
        return format(self.elapsed, format_spec)


T = TypeVar("T")


def retry(func: Callable[[], T], attempts: int = 10, interval: float = 0.5) -> T:
    attempt = 0
    caught_exception: Exception | None = None
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


def concat_files(files: list[Path], target: Path) -> None:
    with open(target, "w") as fh:
        for item in files:
            with open(item) as infile:
                for line in infile:
                    fh.write(line)


def concat_files_to_str(files: list[Path]) -> str:
    concat_str = ""
    for item in files:
        with open(item) as infile:
            for line in infile:
                concat_str += line
    return concat_str


def suppress_exception(
    callback: Callable[[], T],
    logger_: Callable[[Exception], None],
) -> T | None:
    try:
        return callback()
    except Exception as e:
        logger_(e)
        return None


def current_time() -> datetime.datetime:
    return datetime.datetime.now(datetime.UTC).replace(tzinfo=None)


def remove_first_match(elements: list[T], predicate: Callable[[T], bool]) -> None:
    """
    Removes 1st element matching the predicate
    """
    elt = next((elt for elt in elements if predicate(elt)), None)
    if elt:
        elements.remove(elt)
