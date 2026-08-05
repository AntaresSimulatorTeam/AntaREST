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
from antarest.launcher.model import LauncherLoad
from antarest.maintenance.app import MaintenanceTask, TaskName, celery_app
from antarest.maintenance.tasks.common import BackGroundTaskStatus

logger = logging.getLogger(__name__)


class LauncherCacheTaskResult(BaseModel):
    status: BackGroundTaskStatus
    duration_seconds: float
    error: str | None = None


@celery_app.task(base=MaintenanceTask, bind=True, name=TaskName.CACHE_LAUNCHER_LOAD, pydantic=True)
def save_launcher_cache_task(self: MaintenanceTask) -> LauncherCacheTaskResult:
    logger.info("Saving launchers caches to database")
    load_service = self.context.load_service

    start_time = time.time()
    try:
        with db():
            all_launchers_cache_dto_by_id = load_service.get_cacheable_loads()
            launchers_cache = [
                LauncherLoad.from_dto(load_cache, load_name)
                for load_name, load_cache in all_launchers_cache_dto_by_id.items()
            ]
            load_service.launcher_cache_repository.update_all_launcher_loads(launchers_cache)
        expected_launcher_ids = load_service.get_cacheable_loads_names()
        status = (
            BackGroundTaskStatus.SUCCESS
            if all_launchers_cache_dto_by_id.keys() >= set(expected_launcher_ids)
            else BackGroundTaskStatus.PARTIAL_SUCCESS
        )
        return LauncherCacheTaskResult(
            status=status,
            duration_seconds=time.time() - start_time,
        )
    except Exception as e:
        logger.error("Launcher cache task failed", exc_info=e)
        return LauncherCacheTaskResult(
            status=BackGroundTaskStatus.ERROR,
            duration_seconds=time.time() - start_time,
            error=str(e),
        )
