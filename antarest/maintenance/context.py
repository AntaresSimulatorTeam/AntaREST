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

This module provides a singleton context that initializes all required services
(MatrixService, BlobService, StudyService, etc.) when the worker starts.

Each Celery task retrieves services from this context instead of recreating them.
"""

import logging
from pathlib import Path
from typing import TYPE_CHECKING, Optional, cast

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
    Singleton context for maintenance tasks.

    Provides access to all services needed by maintenance tasks:
    - MatrixService
    - BlobService
    - ...

    The context is initialized once per worker process in the worker_init signal.
    Note: No thread synchronization is needed because worker_init is called only once
    at worker startup, and tasks run sequentially within a worker process.
    """

    _INSTANCE: Optional["MaintenanceContext"] = None

    def __init__(self) -> None:
        self.config: Optional["Config"] = None
        self.core_services: Optional["CoreServices"] = None

    @classmethod
    def get_instance(cls) -> "MaintenanceContext":
        """Get or create the singleton instance."""
        if cls._INSTANCE is None:
            cls._INSTANCE = MaintenanceContext()
        return cls._INSTANCE

    def initialize(self, config: "Config", config_path: Path) -> None:
        """
        Initialize the context with config and services.

        This is called automatically by worker_init signal (once per worker).

        Args:
            config: Already loaded Config object
            config_path: Path to application.yaml (needed for DB engine initialization)
        """
        if self.core_services is not None:
            logger.debug("MaintenanceContext already initialized")
            return

        logger.info(f"Initializing MaintenanceContext from {config_path}")

        self.config = config

        engine = init_db_engine(config_path, self.config, auto_upgrade_db=False)
        DBSessionMiddleware(None, custom_engine=engine, session_args=cast(dict[str, bool], SESSION_ARGS))

        self.core_services = create_core_services(app_ctxt=None, config=self.config)

        logger.info("MaintenanceContext initialized successfully")

    def set_core_services(self, config: "Config", core_services: "CoreServices") -> None:
        """
        Directly set the core services (for testing).

        Args:
            config: Config object
            core_services: Pre-built CoreServices instance
        """
        self.config = config
        self.core_services = core_services

    @property
    def matrix_service(self) -> "MatrixService":
        """Get MatrixService."""
        if self.core_services is None:
            raise RuntimeError("MaintenanceContext not initialized")
        return self.core_services.matrix_service

    @property
    def blob_service(self) -> "BlobService":
        """Get BlobService."""
        if self.core_services is None:
            raise RuntimeError("MaintenanceContext not initialized")
        return self.core_services.blob_service
