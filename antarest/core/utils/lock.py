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

"""
Distributed lock implementations.

This module provides lock mechanisms for coordinating between multiple processes or workers.
It defines an abstract interface and concrete implementations for different backends.
"""

import logging
from pathlib import Path
from typing import Callable

from filelock import AcquireReturnProxy, BaseFileLock, FileLock, Timeout
from typing_extensions import override

from antarest.maintenance.config import get_config, load_config

logger = logging.getLogger(__name__)


class LockNotAcquired(Exception):
    """Raised when the lock could not be acquired (another process holds it)."""

    pass


class AntarestFileLock(FileLock):
    """
    A FileLock subclass that raises LockNotAcquired instead of filelock.Timeout
    when the lock cannot be acquired because another process is holding it.
    """

    @override
    def acquire(  # noqa: C901
        self,
        timeout: float | None = None,
        poll_interval: float | None = None,
        *,
        poll_intervall: float | None = None,
        blocking: bool | None = None,
        cancel_check: Callable[[], bool] | None = None,
    ) -> AcquireReturnProxy:
        try:
            return super().acquire(
                timeout, poll_interval, poll_intervall=poll_intervall, blocking=blocking, cancel_check=cancel_check
            )
        except Timeout:
            raise LockNotAcquired(
                f"Could not acquire file lock '{self.lock_file}'. Another thread is probably holding it."
            )


def create_file_lock(lock_id: int, timeout: float = -1, blocking: bool = False) -> BaseFileLock:
    """
    Factory function to create a FileLock instance.
    This locks makes sure that the given file will not be opened by another process.

    Usage:
        with db():
            with create_file_lock(file_lock="my_file.lock", timeout=10, locking=True):
                do_something()

    Args:
        lock_id: Unique integer identifier for this lock
        timeout: the maximum time to wait for the lock, in seconds. -1 means infinite wait
        blocking: If True, wait for lock. If False (default), fail immediately if lock is held.

    Returns:
        A FileLock instance appropriate for the current database.
    """

    load_config()
    config = get_config()
    tmp_folder = config.storage.tmp_dir
    lock_file_path = Path(f"{tmp_folder}/{lock_id}.lock")
    return AntarestFileLock(lock_file=lock_file_path, timeout=timeout, blocking=blocking)
