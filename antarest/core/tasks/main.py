# Copyright (c) 2024, RTE (https://www.rte-france.com)
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

from typing import Optional

from fastapi import FastAPI

from antarest.core.config import Config
from antarest.core.interfaces.eventbus import DummyEventBusService, IEventBus
from antarest.core.tasks.repository import TaskJobRepository
from antarest.core.tasks.service import ITaskService, TaskJobService
from antarest.core.tasks.web import create_tasks_api


def build_taskjob_manager(
    application: Optional[FastAPI],
    config: Config,
    event_bus: IEventBus = DummyEventBusService(),
) -> ITaskService:
    repository = TaskJobRepository()
    service = TaskJobService(config, repository, event_bus)

    if application:
        application.include_router(create_tasks_api(service, config))

    return service
