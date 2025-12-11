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
Celery application instance and configuration.

This module creates the Celery app that will be used by both Beat and Worker.
"""

import logging
import os
import re
from pathlib import Path
from typing import Optional

from celery import Celery
from celery.signals import worker_init

from antarest.core.config import CeleryConfig, Config
from antarest.core.utils.utils import get_local_path
from antarest.maintenance.context import MaintenanceContext

logger = logging.getLogger(__name__)


def _mask_url_credentials(url: str) -> str:
    """Mask password in URL for safe logging."""
    # Matches ://user:password@ and replaces password with ***
    return re.sub(r"(://[^:]+:)[^@]+(@)", r"\1***\2", url)


def _load_config() -> Optional[Config]:
    config_path_str = os.environ.get("ANTAREST_CONF")
    if not config_path_str:
        logger.warning("ANTAREST_CONF not set, using default Celery configuration")
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

_config = _load_config()
if _config and _config.celery:
    _apply_celery_config(celery_app, _config.celery)

celery_app.conf.update(
    # Serialization
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    enable_utc=True,
    # Worker settings
    worker_prefetch_multiplier=1,  # Don't prefetch (tasks can be long)
    worker_max_tasks_per_child=100,  # Restart worker after 100 tasks
    task_acks_late=True,  # Acknowledge after task completion
    task_reject_on_worker_lost=True,  # Reject if worker crashes
    # Timeouts
    task_soft_time_limit=7000,  # 116 min soft limit (warning)
    task_time_limit=7200,  # 2h hard limit (kill)
    # Monitoring
    worker_send_task_events=True,
    task_send_sent_event=True,
    # Routing
    task_routes={
        "antarest.maintenance.tasks.*": {"queue": "maintenance"},
    },
)

# Auto-discover tasks
celery_app.autodiscover_tasks(["antarest.maintenance.tasks"])


@celery_app.on_after_configure.connect
def setup_periodic_tasks(sender: Celery, **kwargs: object) -> None:
    """
    Configure periodic tasks.

    This function is called automatically when Beat scheduler starts.
    It registers all periodic maintenance tasks.
    """
    logger.info("Setting up periodic tasks")

    # Import here to avoid circular imports and get the task signature
    from antarest.maintenance.tasks.gc_matrix_task import clean_matrices_task

    matrix_gc_interval = _config.storage.matrix_gc_sleeping_time if _config else 3600

    sender.add_periodic_task(
        matrix_gc_interval,
        clean_matrices_task.s(),
        name="matrix-gc",
    )

    logger.info(f"Periodic tasks configured successfully (matrix_gc_interval={matrix_gc_interval}s)")


logger.info(
    "Celery app created",
    extra={
        "broker": _mask_url_credentials(celery_app.conf.broker_url or ""),
        "backend": _mask_url_credentials(celery_app.conf.result_backend or ""),
    },
)


@worker_init.connect
def init_worker(**kwargs: object) -> None:
    """
    Initialize worker context on startup.

    This is called ONLY by workers (not by Beat).
    It initializes the MaintenanceContext with all required services.
    Configuration is already loaded at module level (_config).
    """
    config_path_str = os.environ.get("ANTAREST_CONF")
    if _config is None or config_path_str is None:
        logger.warning("No config loaded, worker services may not be available.")
        return

    # Initialize MaintenanceContext with already loaded config
    logger.info("Initializing MaintenanceContext")
    ctx = MaintenanceContext.get_instance()
    ctx.initialize(_config, Path(config_path_str))

    logger.info("Worker initialization complete")
