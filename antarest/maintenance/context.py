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
Dependency injection context for Celery workers.

This module provides a context that holds all required services
(MatrixService, BlobService, etc.) for maintenance tasks.

The context is created once per worker process in the worker_init signal
and stored in the Celery app configuration (app.conf.maintenance_ctx).
Tasks access it via self.app.conf when using bind=True.
"""

import logging
from pathlib import Path
from typing import TYPE_CHECKING, cast

from antarest.core.utils.fastapi_sqlalchemy import DBSessionMiddleware
from antarest.service_creator import SESSION_ARGS, create_core_services, init_db_engine

if TYPE_CHECKING:
    from antarest.blobstore.service import BlobService
    from antarest.core.config import Config
    from antarest.matrixstore.service import MatrixService
    from antarest.service_creator import CoreServices

logger = logging.getLogger(__name__)


class MaintenanceContext:
    """
    Context holding services for maintenance tasks.

    Provides access to all services needed by maintenance tasks:
    - MatrixService
    - BlobService
    - ...

    This is NOT a singleton. An instance is created during worker initialization
    and attached to the Celery app via `app.conf.maintenance_ctx`.
    Tasks access it via `self.app.conf.maintenance_ctx` when using `bind=True`.
    """

    def __init__(self, config: "Config", core_services: "CoreServices") -> None:
        """
        Create a MaintenanceContext with the given config and services.

        Args:
            config: Application configuration
            core_services: Pre-built CoreServices instance containing all services
        """
        self.config = config
        self.core_services = core_services

    @classmethod
    def create(cls, config: "Config", config_path: Path) -> "MaintenanceContext":
        """
        Factory method to create a fully initialized MaintenanceContext.

        This handles database engine initialization and service creation.
        Use this in production (worker_init signal).

        Args:
            config: Already loaded Config object
            config_path: Path to application.yaml (needed for DB engine initialization)

        Returns:
            A fully initialized MaintenanceContext
        """
        logger.info(f"Creating MaintenanceContext from {config_path}")

        engine = init_db_engine(config_path, config, auto_upgrade_db=False)
        DBSessionMiddleware(None, custom_engine=engine, session_args=cast(dict[str, bool], SESSION_ARGS))

        core_services = create_core_services(app_ctxt=None, config=config)

        logger.info("MaintenanceContext created successfully")
        return cls(config=config, core_services=core_services)

    @property
    def matrix_service(self) -> "MatrixService":
        """Get MatrixService."""
        return self.core_services.matrix_service

    @property
    def blob_service(self) -> "BlobService":
        """Get BlobService."""
        return self.core_services.blob_service
