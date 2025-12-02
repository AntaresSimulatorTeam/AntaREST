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
Configuration is loaded from environment variables (for Beat) and can be
overridden from YAML config file (for Worker in worker_init signal).
"""

import logging
import os
import re
from pathlib import Path

from celery import Celery
from celery.signals import worker_init

from antarest.celery.context import MaintenanceContext
from antarest.core.config import Config
from antarest.core.utils.utils import get_local_path

logger = logging.getLogger(__name__)


def _mask_url_credentials(url: str) -> str:
    """Mask password in URL for safe logging."""
    # Matches ://user:password@ and replaces password with ***
    return re.sub(r"(://[^:]+:)[^@]+(@)", r"\1***\2", url)


# Create Celery app instance
celery_app = Celery("antarest-maintenance")

# Configure from environment variables (fallback/default)
# This allows Beat to work with just env vars
celery_app.conf.update(
    # Broker and backend
    broker_url=os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/1"),
    result_backend=os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/1"),
    result_expires=86400,  # 24 hours
    # Serialization
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    # Timezone
    timezone=os.getenv("CELERY_TIMEZONE", "UTC"),
    enable_utc=True,
    # Worker settings (ignored by Beat)
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
    from antarest.maintenance.tasks.gc_matrix import clean_matrices_task

    # Matrix Garbage Collector interval (default: 3600 seconds = 1 hour)
    matrix_gc_interval = int(os.getenv("CELERY_MATRIX_GC_INTERVAL", "3600"))

    sender.add_periodic_task(
        matrix_gc_interval,
        clean_matrices_task.s(),
        name="matrix-gc",
    )

    logger.info(f"Periodic tasks configured successfully (matrix_gc_interval={matrix_gc_interval}s)")


logger.info(
    "Celery app created",
    extra={
        "broker": _mask_url_credentials(celery_app.conf.broker_url),
        "backend": _mask_url_credentials(celery_app.conf.result_backend),
    },
)


@worker_init.connect
def init_worker(**kwargs: object) -> None:
    """
    Initialize worker context on startup.

    This is called ONLY by workers (not by Beat).
    It loads the full configuration from YAML file and initializes
    the MaintenanceContext with all required services.
    """
    # Get config file path from environment
    config_path_str = os.environ.get("ANTAREST_CONF")
    if not config_path_str:
        logger.warning("ANTAREST_CONF not set, worker will use env vars only. Services may not be available.")
        return

    config_path = Path(config_path_str)
    if not config_path.exists():
        logger.error(f"Config file not found: {config_path}")
        return

    # Load config from YAML (only once, then pass to MaintenanceContext)
    logger.info(f"Loading worker config from {config_path}")
    res = get_local_path() / "resources"
    config = Config.from_yaml_file(res=res, file=config_path)

    # Override Celery config from YAML if present (YAML > env vars)
    if config.celery:
        logger.info("Overriding Celery config from YAML file")
        celery_app.conf.update(
            broker_url=config.celery.broker_url,
            result_backend=config.celery.result_backend,
            timezone=config.celery.timezone,
            result_expires=config.celery.result_expires,
        )

    # Initialize MaintenanceContext with already loaded config
    logger.info("Initializing MaintenanceContext")
    ctx = MaintenanceContext.get_instance()
    ctx.initialize(config, config_path)

    logger.info("Worker initialization complete")
