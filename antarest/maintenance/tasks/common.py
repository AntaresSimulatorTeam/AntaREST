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

"""Shared types for maintenance tasks."""

from enum import IntEnum, StrEnum
from typing import Optional

from redis.exceptions import ConnectionError as RedisConnectionError
from sqlalchemy.exc import OperationalError

from antarest.core.serde import AntaresBaseModel
from antarest.core.utils.lock import LockNotAcquired

# Transient errors that should trigger a retry
TRANSIENT_ERRORS = (
    RedisConnectionError,  # Redis connection issues
    OperationalError,  # Database connection issues
    LockNotAcquired,  # Lock already held by another task
    ConnectionError,  # Generic network errors
)


class MaintenanceContextNotFoundError(RuntimeError):
    """Raised when MaintenanceContext is not found in app.conf."""

    def __init__(self) -> None:
        super().__init__("MaintenanceContext not in app.conf - worker not initialized?")


class BackGroundTaskStatus(StrEnum):
    SUCCESS = "success"
    PARTIAL_SUCCESS = "partial_success"
    SKIPPED = "skipped"
    ERROR = "error"


class GarbageCollectorTaskResult(AntaresBaseModel):
    """Result of a garbage collector task run."""

    status: BackGroundTaskStatus
    deleted_count: int
    failed_count: int = 0
    duration_seconds: float
    dry_run: Optional[bool] = None
    reason: Optional[str] = None
    error: Optional[str] = None


class LockId(IntEnum):
    """PostgreSQL advisory lock IDs to prevent concurrent runs."""

    MATRIX_GC = 1001
    BLOB_GC = 1002
    AUTO_ARCHIVE = 1003
    WATCHER_SCAN = 1004
    VARIABLE_VIEW_GC = 1005


class WatcherScanTaskResult(AntaresBaseModel):
    """Result of a watcher scan task run."""

    status: BackGroundTaskStatus
    studies_found: int
    duration_seconds: float
    dry_run: bool = False
    reason: Optional[str] = None
    error: Optional[str] = None
