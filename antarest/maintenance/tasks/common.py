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

"""Shared types for maintenance tasks."""

from enum import IntEnum, StrEnum
from typing import Optional

from pydantic import BaseModel


class TaskStatus(StrEnum):
    SUCCESS = "success"
    PARTIAL_SUCCESS = "partial_success"
    SKIPPED = "skipped"
    ERROR = "error"


class GarbageCollectorTaskResult(BaseModel):
    """Result of a garbage collector task run."""

    status: TaskStatus
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
