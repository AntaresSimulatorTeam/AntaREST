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
from typing import TYPE_CHECKING

from antarest.core.tasks.service import ITaskService
from antarest.core.utils.fastapi_sqlalchemy.middleware import init_db_singleton
from antarest.service_creator import SESSION_ARGS, Services, create_services, init_db_engine
from antarest.study.repository import StudyDiskSpaceRepository

if TYPE_CHECKING:
    from antarest.blobstore.service import BlobService
    from antarest.core.config import Config
    from antarest.matrixstore.service import MatrixService
    from antarest.output.service import OutputService
    from antarest.study.service import StudyService

logger = logging.getLogger(__name__)


class MaintenanceContext:
    """Holds services needed by maintenance tasks."""

    def __init__(self, config: "Config", services: "Services") -> None:
        self.config = config
        self.services = services

    @classmethod
    def create(cls, config: "Config") -> "MaintenanceContext":
        """Initialize DB and services, return a ready-to-use context."""
        logger.info("Initializing MaintenanceContext")

        engine = init_db_engine(config, auto_upgrade_db=False)
        init_db_singleton(custom_engine=engine, session_args=SESSION_ARGS)
        services = create_services(config=config)

        return cls(config, services)

    @property
    def matrix_service(self) -> "MatrixService":
        return self.services.matrix

    @property
    def blob_service(self) -> "BlobService":
        return self.services.blob

    @property
    def study_service(self) -> "StudyService":
        return self.services.study

    @property
    def output_service(self) -> "OutputService":
        return self.services.output

    @property
    def task_service(self) -> "ITaskService":
        return self.services.task

    @property
    def study_disk_space_repository(self) -> "StudyDiskSpaceRepository":
        return self.services.study_disk_space_repository
