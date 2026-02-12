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
Celery app for maintenance tasks.

Architecture:
- Import time: Create Celery app + apply broker config (required for Beat/Worker to connect)
- celeryd_init signal: Full config loading
- on_after_configure signal: Register periodic tasks (Beat only)
- worker_init signal: Create MaintenanceContext (Worker only)
"""

import logging
import os
import re
from enum import StrEnum
from pathlib import Path
from typing import Any

from celery import Celery
from celery.signals import celeryd_init, setup_logging, task_failure, worker_init

from antarest.core.config import CeleryConfig, Config
from antarest.core.exceptions import ConfigurationError
from antarest.core.logging.utils import configure_logger
from antarest.core.utils.utils import get_local_path
from antarest.maintenance.context import MaintenanceContext

logger = logging.getLogger(__name__)

MAINTENANCE_QUEUE = "maintenance"


class TaskName(StrEnum):
    WATCHER_SCAN = "watcher_scan"
    MATRICES_CLEANER = "matrices_cleaner"
    BLOBS_CLEANER = "blobs_cleaner"
    AUTO_ARCHIVER = "auto_archiver"
    VARIABLE_VIEW_CLEANER = "variable_view_cleaner"


def _mask_url_credentials(url: str) -> str:
    """Mask password in URL for safe logging."""
    return re.sub(r"(://[^:]*:)[^@]+(@)", r"\1***\2", url)


def _load_config() -> Config:
    """
    Load config from ANTAREST_CONF env var, else we abort the startup.
    """
    config_path_str = os.environ.get("ANTAREST_CONF")

    if not config_path_str or not Path(config_path_str).exists():
        raise ConfigurationError(
            "You must provide a path to the YAML configuration file through the ANTAREST_CONF env variable the to "
            "start celery app."
        )
    config_path = Path(config_path_str)
    res = get_local_path() / "resources"
    return Config.from_yaml_file(res=res, file=config_path)


def _apply_celery_config(app: Celery, celery_config: CeleryConfig) -> None:
    app.conf.update(
        broker_url=celery_config.broker_url,
        result_backend=celery_config.result_backend,
        result_expires=celery_config.result_expires,
    )


celery_app = Celery("antarest-maintenance")

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    enable_utc=True,
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=100,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    task_soft_time_limit=6600,
    task_time_limit=7200,
    worker_send_task_events=True,
    task_send_sent_event=True,
    task_routes={name: {"queue": MAINTENANCE_QUEUE} for name in TaskName},
)

celery_app.autodiscover_tasks(["antarest.maintenance.tasks"])

_config = _load_config()
_apply_celery_config(celery_app, _config.celery)


@setup_logging.connect
def _setup_logging(**_: Any) -> None:
    """
    It's important to use that celery signal, otherwise celery overrides some of our logging configuration.
    """
    configure_logger(_config)


@celeryd_init.connect
def _configure_celery(sender: str, **_: Any) -> None:
    """Full initialization when Celery worker starts."""
    logger.info(f"Broker: {_mask_url_credentials(celery_app.conf.broker_url or '')}")
    celery_app.conf.antarest_config = _config


@celery_app.on_after_configure.connect
def _setup_periodic_tasks(sender: Celery, **_: Any) -> None:
    """Register periodic maintenance tasks (called by Beat on startup)."""
    from antarest.maintenance.tasks.auto_archive_task import setup_auto_archive_task
    from antarest.maintenance.tasks.gc_blob_task import clean_blobs_task
    from antarest.maintenance.tasks.gc_matrix_task import clean_matrices_task
    from antarest.maintenance.tasks.gc_variable_view_task import clean_variable_views_task
    from antarest.maintenance.tasks.watcher_scan_task import watcher_scan_task

    storage = _config.storage

    sender.add_periodic_task(storage.matrix_gc_sleeping_time, clean_matrices_task.s(), name=TaskName.MATRICES_CLEANER)
    sender.add_periodic_task(storage.blob_gc_sleeping_time, clean_blobs_task.s(), name=TaskName.BLOBS_CLEANER)
    setup_auto_archive_task(sender, storage)
    sender.add_periodic_task(storage.watcher_scan_sleeping_time, watcher_scan_task.s(), name=TaskName.WATCHER_SCAN)
    sender.add_periodic_task(
        storage.variable_view_gc_sleeping_time, clean_variable_views_task.s(), name=TaskName.VARIABLE_VIEW_CLEANER
    )

    logger.info(
        f"Periodic tasks registered: matrix_gc={storage.matrix_gc_sleeping_time}s, "
        f"blob_gc={storage.blob_gc_sleeping_time}s, "
        f"watcher_scan={storage.watcher_scan_sleeping_time}s, variable_view_gc={storage.variable_view_gc_sleeping_time}s"
    )


@worker_init.connect
def _init_worker(**_: Any) -> None:
    """Create MaintenanceContext (Worker only, not Beat)."""
    ctx = MaintenanceContext.create(_config)
    celery_app.conf.maintenance_ctx = ctx
    logger.info("Worker ready")


@task_failure.connect
def _log_critical_task_failure(sender: Any, task_id: str, exception: Exception, **kwargs: Any) -> None:
    """Log critical failures for tasks that run infrequently."""
    if sender and sender.name == TaskName.AUTO_ARCHIVER:
        logger.critical(
            f"CRITICAL: Auto-archive task [{task_id}] failed permanently after all retries. Exception: {exception}. ",
            exc_info=exception,
        )
