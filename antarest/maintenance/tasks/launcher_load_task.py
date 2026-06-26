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

import logging
import time

from pydantic import BaseModel

from antarest.core.utils.fastapi_sqlalchemy import db
from antarest.launcher.adapters.database_launcher_load_dao import DataBaseLauncherLoadDao
from antarest.launcher.main import build_launcher
from antarest.maintenance.app import MaintenanceTask, TaskName, celery_app
from antarest.maintenance.tasks.common import BackGroundTaskStatus

logger = logging.getLogger(__name__)


class LauncherLoadTaskResult(BaseModel):
    status: BackGroundTaskStatus
    duration_seconds: float
    error: str | None = None


@celery_app.task(base=MaintenanceTask, bind=True, name=TaskName.LAUNCHER_LOAD, pydantic=True)
def save_launcher_load_task(self: MaintenanceTask) -> LauncherLoadTaskResult:
    ctx = self.context
    logger.info("Saving launcher load state to database")
    launcher_service = build_launcher(
        ctx.config,
        study_service=ctx.core_services.study_service,
        output_service=ctx.core_services.output_service,
        login_service=ctx.core_services.login_service,
        event_bus=ctx.core_services.event_bus,
        task_service=ctx.core_services.task_service,
        file_transfer_manager=ctx.core_services.file_transfer_manager,
        cache=ctx.core_services.cache,
    )

    if launcher_service is None:
        return LauncherLoadTaskResult(
            status=BackGroundTaskStatus.ERROR,
            duration_seconds=0,
            error="Launcher not found",
        )
    start_time = time.time()
    try:
        with db():
            dao = DataBaseLauncherLoadDao()
            dao.update_all_launcher_loads(launcher_service)
        return LauncherLoadTaskResult(
            status=BackGroundTaskStatus.SUCCESS,
            duration_seconds=time.time() - start_time,
        )
    except Exception as e:
        logger.error("Launcher load task failed", exc_info=e)
        return LauncherLoadTaskResult(
            status=BackGroundTaskStatus.ERROR,
            duration_seconds=time.time() - start_time,
            error=str(e),
        )
