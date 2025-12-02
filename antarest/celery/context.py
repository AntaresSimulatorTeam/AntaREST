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
import threading
from pathlib import Path
from typing import TYPE_CHECKING, Optional

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
    """

    _instance: Optional["MaintenanceContext"] = None
    _lock = threading.Lock()

    def __init__(self) -> None:
        self.config: Optional["Config"] = None
        self.core_services: Optional["CoreServices"] = None
        self._initialized = False

    @classmethod
    def get_instance(cls) -> "MaintenanceContext":
        """Get or create the singleton instance (thread-safe)."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = MaintenanceContext()
        return cls._instance

    def initialize(self, config: "Config", config_path: Path) -> None:
        """
        Initialize the context with config and services.

        This is called automatically by worker_init signal.

        Args:
            config: Already loaded Config object
            config_path: Path to application.yaml (needed for DB engine initialization)
        """
        if self._initialized:
            logger.debug("MaintenanceContext already initialized")
            return

        with self._lock:
            if self._initialized:
                return

            logger.info(f"Initializing MaintenanceContext from {config_path}")

            # Import here to avoid circular dependencies
            from typing import Dict, cast

            from antarest.core.utils.fastapi_sqlalchemy import DBSessionMiddleware
            from antarest.service_creator import SESSION_ARGS, create_core_services, init_db_engine

            self.config = config

            # Initialize database session middleware (required for db() context manager)
            engine = init_db_engine(config_path, self.config, auto_upgrade_db=False)
            DBSessionMiddleware(None, custom_engine=engine, session_args=cast(Dict[str, bool], SESSION_ARGS))

            # Create services using existing factories
            # app_ctxt=None because we're not in a FastAPI context
            self.core_services = create_core_services(app_ctxt=None, config=self.config)

            self._initialized = True
            logger.info("MaintenanceContext initialized successfully")

    @property
    def matrix_service(self) -> "MatrixService":
        """Get MatrixService."""
        if not self._initialized or self.core_services is None:
            raise RuntimeError("MaintenanceContext not initialized")
        return self.core_services.matrix_service

    @property
    def blob_service(self) -> "BlobService":
        """Get BlobService."""
        if not self._initialized or self.core_services is None:
            raise RuntimeError("MaintenanceContext not initialized")
        return self.core_services.blob_service
