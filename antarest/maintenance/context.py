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

import asyncio
import logging
from typing import TYPE_CHECKING

from antarest.core.tasks.service import ITaskService
from antarest.core.utils.fastapi_sqlalchemy.middleware import init_db_singleton
from antarest.dishka_provider import make_container
from antarest.service_creator import SESSION_ARGS, init_db_engine

if TYPE_CHECKING:
    from dishka import AsyncContainer

    from antarest.blobstore.service import BlobService
    from antarest.core.config import Config
    from antarest.matrixstore.service import MatrixService
    from antarest.output.output_service import OutputService
    from antarest.study.service import StudyService

logger = logging.getLogger(__name__)


class MaintenanceContext:
    """Holds services needed by maintenance tasks."""

    def __init__(self, config: "Config", container: "AsyncContainer") -> None:
        self.config = config
        self._container = container

    @classmethod
    def create(cls, config: "Config") -> "MaintenanceContext":
        """Initialize DB and services, return a ready-to-use context."""
        logger.info("Initializing MaintenanceContext")

        engine = init_db_engine(config, auto_upgrade_db=False)
        init_db_singleton(custom_engine=engine, session_args=SESSION_ARGS)
        container = make_container(config)

        return cls(config, container)

    def _get(self, service_type: type):
        return asyncio.run(self._container.get(service_type))

    @property
    def matrix_service(self) -> "MatrixService":
        from antarest.matrixstore.service import MatrixService

        return self._get(MatrixService)

    @property
    def blob_service(self) -> "BlobService":
        from antarest.blobstore.service import BlobService

        return self._get(BlobService)

    @property
    def study_service(self) -> "StudyService":
        from antarest.study.service import StudyService

        return self._get(StudyService)

    @property
    def output_service(self) -> "OutputService":
        from antarest.output.output_service import OutputService

        return self._get(OutputService)

    @property
    def task_service(self) -> "ITaskService":
        return self._get(ITaskService)
