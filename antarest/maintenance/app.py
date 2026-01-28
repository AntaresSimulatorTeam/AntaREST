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

This design allows the module to be imported without side effects, making it
easier to test and avoiding issues with config loading during imports.
"""

import logging
import os
import re
from pathlib import Path
from typing import Any, Optional

from celery import Celery
from celery.signals import celeryd_init, setup_logging, worker_init

from antarest.core.config import CeleryConfig, Config
from antarest.core.logging.utils import configure_logger
from antarest.core.utils.utils import get_local_path
from antarest.maintenance.context import MaintenanceContext

logger = logging.getLogger(__name__)


def _mask_url_credentials(url: str) -> str:
    """Mask password in URL for safe logging."""
    # Matches ://user:password@ or ://:password@ and replaces password with ***
    return re.sub(r"(://[^:]*:)[^@]+(@)", r"\1***\2", url)


def _load_config() -> Optional[Config]:
    """Load config from ANTAREST_CONF env var, or return None."""
    config_path_str = os.environ.get("ANTAREST_CONF")
    if not config_path_str:
        logger.warning("ANTAREST_CONF not set, using defaults")
        return None

    config_path = Path(config_path_str)
    if not config_path.exists():
        logger.error(f"Config file not found: {config_path}")
        return None

    res = get_local_path() / "resources"
    return Config.from_yaml_file(res=res, file=config_path)


def _apply_celery_config(app: Celery, celery_config: CeleryConfig) -> None:
    app.conf.update(
        broker_url=celery_config.broker_url,
        result_backend=celery_config.result_backend,
        result_expires=celery_config.result_expires,
    )


celery_app = Celery("antarest-maintenance")

# Load broker config immediately (needed for Beat, not just workers)
_startup_config = _load_config()
if _startup_config and _startup_config.celery:
    _apply_celery_config(celery_app, _startup_config.celery)

# Get storage config for beat_schedule
_storage_config = _startup_config.storage if _startup_config else None

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    enable_utc=True,
    worker_prefetch_multiplier=1,  # Don't prefetch (tasks can be long)
    worker_max_tasks_per_child=100,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    task_soft_time_limit=7000,  # ~2h soft limit
    task_time_limit=7200,  # 2h hard limit
    worker_send_task_events=True,
    task_send_sent_event=True,
    task_routes={"antarest.maintenance.tasks.*": {"queue": "maintenance"}},
    # Define beat_schedule directly (more reliable than on_after_configure signal)
    beat_schedule={
        "matrices_cleaner": {
            "task": "matrices_cleaner",
            "schedule": _storage_config.matrix_gc_sleeping_time if _storage_config else 3600,
        },
        "blobs_cleaner": {
            "task": "blobs_cleaner",
            "schedule": _storage_config.blob_gc_sleeping_time if _storage_config else 86400,
        },
        "auto_archiver": {
            "task": "auto_archiver",
            "schedule": _storage_config.auto_archive_sleeping_time if _storage_config else 3600,
        },
        "watcher_scan": {
            "task": "watcher_scan",
            "schedule": _storage_config.watcher_scan_sleeping_time if _storage_config else 60,
        },
        "variable_view_cleaner": {
            "task": "variable_view_cleaner",
            "schedule": _storage_config.variable_view_gc_sleeping_time if _storage_config else 3600,
        },
    },
)

# Store config for later use
if _startup_config:
    celery_app.conf.antarest_config = _startup_config

celery_app.autodiscover_tasks(["antarest.maintenance.tasks"])


@setup_logging.connect
def _setup_logging(**_: Any) -> None:
    # Prevent Celery from hijacking our logging config
    pass


@celeryd_init.connect
def _configure_from_environment(sender: str, conf: Any, **_: object) -> None:
    """Load config when Celery process starts."""
    logger.info(f"Configuring Celery for {sender}")

    config = _load_config()
    if not config:
        logger.warning("No config loaded, using defaults")
        return

    if config.celery:
        _apply_celery_config(celery_app, config.celery)
        logger.info(f"Broker: {_mask_url_credentials(celery_app.conf.broker_url or '')}")

    configure_logger(config)
    celery_app.conf.antarest_config = config
    logger.info("Celery configured")


@celery_app.on_after_configure.connect
def _setup_periodic_tasks(sender: Celery, **_: object) -> None:
    """Trigger initial tasks on startup (schedule is defined in beat_schedule config)."""
    from antarest.maintenance.tasks.auto_archive_task import auto_archive_task
    from antarest.maintenance.tasks.gc_blob_task import clean_blobs_task
    from antarest.maintenance.tasks.gc_matrix_task import clean_matrices_task

    # Stagger first execution to avoid hitting everything at once
    clean_matrices_task.apply_async(countdown=60)
    clean_blobs_task.apply_async(countdown=90)
    auto_archive_task.apply_async(countdown=120)

    logger.info("Periodic tasks configured via beat_schedule")


@worker_init.connect
def _init_worker(sender: Celery, **_: object) -> None:
    """Create MaintenanceContext for workers (not Beat)."""
    config_path_str = os.environ.get("ANTAREST_CONF")
    config: Optional[Config] = getattr(celery_app.conf, "antarest_config", None)

    if not config or not config_path_str:
        logger.warning("No config, worker services won't be available")
        return

    ctx = MaintenanceContext.create(config, Path(config_path_str))
    celery_app.conf.maintenance_ctx = ctx
    logger.info("Worker ready")
