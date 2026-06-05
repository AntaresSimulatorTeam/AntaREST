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

"""Disk usage logging task."""

import logging
import shutil

from prometheus_client import REGISTRY, CollectorRegistry, Gauge
from pydantic import BaseModel

from antarest.core.config import Config
from antarest.core.metrics import WORKER_ID
from antarest.core.utils.fastapi_sqlalchemy import db
from antarest.core.utils.lock import LockNotAcquired, create_file_lock
from antarest.maintenance.tasks.common import BackGroundTaskStatus, LockId

logger = logging.getLogger(__name__)


class DiskUsageTaskResult(BaseModel):
    status: BackGroundTaskStatus


class WorkspaceDiskUsageMetrics:
    def __init__(self, registry: CollectorRegistry) -> None:
        self._disk_used_gauge = Gauge(
            "workspaces_disk_used_bytes",
            "Disk usage in bytes",
            ["worker_id", "workspace"],
            multiprocess_mode="liveall",
            registry=registry,
        )
        self._disk_free_gauge = Gauge(
            "workspaces_disk_free_bytes",
            "Free disk space in bytes",
            ["worker_id", "workspace"],
            multiprocess_mode="liveall",
            registry=registry,
        )
        self._disk_total_gauge = Gauge(
            "workspaces_disk_total_bytes",
            "Total disk space in bytes",
            ["worker_id", "workspace"],
            multiprocess_mode="liveall",
            registry=registry,
        )

    def update_disk_usage(self, workspace: str, free: int, used: int, total: int) -> None:
        self._disk_free_gauge.labels(WORKER_ID, workspace).set(free)
        self._disk_used_gauge.labels(WORKER_ID, workspace).set(used)
        self._disk_total_gauge.labels(WORKER_ID, workspace).set(total)


def check_disk_usage(config: Config) -> None:
    for name, workspace in config.storage.workspaces.items():
        try:
            usage = shutil.disk_usage(workspace.path)
            logger.info(
                f"Disk usage for {name}: {(100 * usage.used / usage.total):.2f}%"
                f" ({(usage.free / 1000000000):.3f}GB free)"
            )

            metrics = WorkspaceDiskUsageMetrics(REGISTRY) if config.metrics.prometheus else None

            if metrics:
                metrics.update_disk_usage(name, free=usage.free, used=usage.used, total=usage.total)

        except Exception as e:
            logger.error(
                f"Failed to check disk usage for disk {workspace.path}",
                exc_info=e,
            )


def disk_usage_logging(config: Config) -> DiskUsageTaskResult:
    try:
        with db():
            with create_file_lock(LockId.DISK_USAGE, lock_folder=config.storage.tmp_dir):
                logger.info("Starting disk usage logging")
                check_disk_usage(config)
                logger.info("Disk usage logging finished")

    except LockNotAcquired:
        logger.warning(f"Could not acquire lock {LockId.DISK_USAGE}, another disk usage logging is probably running")
        return DiskUsageTaskResult(
            status=BackGroundTaskStatus.SKIPPED,
        )

    return DiskUsageTaskResult(
        status=BackGroundTaskStatus.SUCCESS,
    )
