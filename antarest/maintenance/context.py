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
Context holding services for Celery maintenance workers.

Created once per worker in worker_init and stored in app.conf.maintenance_ctx.
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
    from antarest.study.output.output_service import OutputService
    from antarest.study.service import StudyService

logger = logging.getLogger(__name__)


class MaintenanceContext:
    """Holds services needed by maintenance tasks."""

    def __init__(self, config: "Config", core_services: "CoreServices") -> None:
        self.config = config
        self.core_services = core_services

    @classmethod
    def create(cls, config: "Config", config_path: Path) -> "MaintenanceContext":
        """Initialize DB and services, return a ready-to-use context."""
        logger.info(f"Initializing MaintenanceContext from {config_path}")

        engine = init_db_engine(config_path, config, auto_upgrade_db=False)
        DBSessionMiddleware(None, custom_engine=engine, session_args=cast(dict[str, bool], SESSION_ARGS))
        core_services = create_core_services(app_ctxt=None, config=config)

        return cls(config, core_services)

    @property
    def matrix_service(self) -> "MatrixService":
        return self.core_services.matrix_service

    @property
    def blob_service(self) -> "BlobService":
        return self.core_services.blob_service

    @property
    def study_service(self) -> "StudyService":
        return self.core_services.study_service

    @property
    def output_service(self) -> "OutputService":
        return self.core_services.output_service
