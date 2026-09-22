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

import prometheus_client

from antarest.core.config import Config
from antarest.core.interfaces.eventbus import DummyEventBusService, IEventBus
from antarest.core.metrics import TasksMetricsRecorder
from antarest.core.tasks.repository import TaskJobRepository
from antarest.core.tasks.service import ITaskService, TaskJobService


def build_taskjob_manager(
    config: Config,
    event_bus: IEventBus = DummyEventBusService(),
) -> ITaskService:
    repository = TaskJobRepository()

    listeners = []
    if config.metrics.prometheus:
        listeners.append(TasksMetricsRecorder(prometheus_client.REGISTRY))

    service = TaskJobService(config, repository, event_bus, listeners=listeners)

    return service
