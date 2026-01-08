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

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    enable_utc=True,
    worker_prefetch_multiplier=1, # Don't prefetch (tasks can be long)
    worker_max_tasks_per_child=100,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    task_soft_time_limit=7000,  # ~2h soft limit
    task_time_limit=7200,  # 2h hard limit
    worker_send_task_events=True,
    task_send_sent_event=True,
    task_routes={"antarest.maintenance.tasks.*": {"queue": "maintenance"}},
)

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
    """Register periodic maintenance tasks (called by Beat on startup)."""
    from antarest.core.config import StorageConfig
    from antarest.maintenance.tasks.auto_archive_task import auto_archive_task
    from antarest.maintenance.tasks.gc_blob_task import clean_blobs_task
    from antarest.maintenance.tasks.gc_matrix_task import clean_matrices_task

    config: Optional[Config] = getattr(celery_app.conf, "antarest_config", None)
    storage = config.storage if config else StorageConfig()

    sender.add_periodic_task(storage.matrix_gc_sleeping_time, clean_matrices_task.s(), name="matrices_cleaner")
    sender.add_periodic_task(storage.blob_gc_sleeping_time, clean_blobs_task.s(), name="blobs_cleaner")
    sender.add_periodic_task(storage.auto_archive_sleeping_time, auto_archive_task.s(), name="auto_archiver")

    # Stagger first execution to avoid hitting everything at once
    clean_matrices_task.apply_async(countdown=60)
    clean_blobs_task.apply_async(countdown=90)
    auto_archive_task.apply_async(countdown=120)

    logger.info(
        f"Periodic tasks: matrix_gc={storage.matrix_gc_sleeping_time}s, "
        f"blob_gc={storage.blob_gc_sleeping_time}s, auto_archive={storage.auto_archive_sleeping_time}s"
    )


@worker_init.connect
def _init_worker(sender: Celery, **_: object) -> None:
    """Create MaintenanceContext for workers (not Beat)."""
    config_path_str = os.environ.get("ANTAREST_CONF")
    config: Optional[Config] = getattr(celery_app.conf, "antarest_config", None)

    if not config or not config_path_str:
        logger.warning("No config, worker services won't be available")
        return

    ctx = MaintenanceContext.create(config, Path(config_path_str))
    sender.conf.maintenance_ctx = ctx
    logger.info("Worker ready")
