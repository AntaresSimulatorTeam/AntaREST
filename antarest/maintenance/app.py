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

Configuration is loaded lazily via Celery signals to avoid side effects at import time:
- `celeryd_init`: Loads config from ANTAREST_CONF and applies Celery-specific settings
- `worker_init`: Creates the MaintenanceContext with all services
- `on_after_configure`: Registers periodic tasks (Beat only)

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
    """
    Load configuration from ANTAREST_CONF environment variable.

    Returns:
        Config object if loaded successfully, None otherwise.
    """
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
    """Apply Celery-specific configuration (broker, backend, etc.)."""
    app.conf.update(
        broker_url=celery_config.broker_url,
        result_backend=celery_config.result_backend,
        result_expires=celery_config.result_expires,
    )


# =============================================================================
# Celery App Creation (minimal, no side effects)
# =============================================================================

celery_app = Celery("antarest-maintenance")

# Static configuration that doesn't depend on external config files
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

# Auto-discover tasks (static, no side effects)
celery_app.autodiscover_tasks(["antarest.maintenance.tasks"])


# =============================================================================
# Celery Signals (lazy initialization)
# =============================================================================


@setup_logging.connect
def _setup_logging(**kwargs: Any) -> None:
    """
    Prevent Celery from overwriting our logging configuration.

    This signal handler is intentionally empty - its presence tells Celery
    not to configure logging itself.
    """
    pass


@celeryd_init.connect
def _configure_from_environment(sender: str, conf: Any, **kwargs: object) -> None:
    """
    Load and apply configuration when the Celery process starts.

    This is called early in the Celery worker/beat startup, before worker_init.
    It loads the AntaREST config and applies Celery-specific settings.

    The config is stored in app.conf.antarest_config for later use by
    worker_init and setup_periodic_tasks.

    Args:
        sender: Name of the worker/beat process
        conf: Celery configuration object
    """
    logger.info(f"Configuring Celery app for {sender}")

    config = _load_config()
    if config is None:
        logger.warning("No config loaded, using default settings")
        return

    # Apply Celery-specific config (broker, backend)
    if config.celery:
        _apply_celery_config(celery_app, config.celery)
        logger.info(
            "Celery config applied",
            extra={
                "broker": _mask_url_credentials(celery_app.conf.broker_url or ""),
                "backend": _mask_url_credentials(celery_app.conf.result_backend or ""),
            },
        )

    # Configure logging
    configure_logger(config)

    # Store config in app.conf for later use
    celery_app.conf.antarest_config = config

    logger.info("Celery app configured successfully")


@celery_app.on_after_configure.connect
def _setup_periodic_tasks(sender: Celery, **kwargs: object) -> None:
    """
    Configure periodic tasks.

    This function is called automatically when Beat scheduler starts.
    It registers all periodic maintenance tasks.

    Args:
        sender: The Celery app instance
    """
    logger.info("Setting up periodic tasks")

    # Import here to avoid circular imports
    from antarest.maintenance.tasks.gc_matrix_task import clean_matrices_task
    from antarest.maintenance.tasks.gc_variable_view_task import clean_variable_views_task

    # Get config from app.conf (set by _configure_from_environment)
    config: Optional[Config] = getattr(celery_app.conf, "antarest_config", None)
    matrix_gc_interval = config.storage.matrix_gc_sleeping_time if config else 3600
    vbv_output_gc_interval = config.storage.vbv_output_gc_sleeping_time if config else 3600

    # Register periodic tasks
    sender.add_periodic_task(
        matrix_gc_interval,
        clean_matrices_task.s(),
        name="matrix-gc",
    )

    sender.add_periodic_task(
        vbv_output_gc_interval,
        clean_variable_views_task.s(),
        name="vbv-output-gc",
    )

    # Schedule first execution shortly after startup (60 seconds to let workers initialize)
    clean_matrices_task.apply_async(countdown=60)
    clean_variable_views_task.apply_async(countdown=90)

    logger.info(
        f"Periodic tasks configured successfully "
        f"(matrix_gc_interval={matrix_gc_interval}s, vbv_output_gc_interval={vbv_output_gc_interval}s)"
    )


@worker_init.connect
def _init_worker(sender: Celery, **kwargs: object) -> None:
    """
    Initialize worker context on startup.

    This is called ONLY by workers (not by Beat), after celeryd_init.
    It creates a MaintenanceContext with all required services and attaches it
    to the Celery app configuration so tasks can access it via self.app.conf.

    Args:
        sender: The Celery app instance
    """
    config_path_str = os.environ.get("ANTAREST_CONF")
    config: Optional[Config] = getattr(celery_app.conf, "antarest_config", None)

    if config is None or config_path_str is None:
        logger.warning("No config loaded, worker services may not be available.")
        return

    # Create MaintenanceContext and attach to app.conf
    logger.info("Creating MaintenanceContext")
    ctx = MaintenanceContext.create(config, Path(config_path_str))
    sender.conf.maintenance_ctx = ctx

    logger.info("Worker initialization complete")
