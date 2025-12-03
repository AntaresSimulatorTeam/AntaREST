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
from threading import Thread

from antarest.core.config import Config, RemoteWorkerConfig
from antarest.core.interfaces.eventbus import Event, EventType
from antarest.core.model import PermissionInfo, PublicMode
from antarest.core.remote.remote_executor import RemoteWorkerExecutor
from antarest.core.tasks.model import TaskResult, TaskType
from antarest.eventbus.business.local_eventbus import LocalEventBus
from antarest.eventbus.service import EventBusService
from antarest.worker.worker import WorkerTaskCommand, WorkerTaskResult


def test_remote_executor():
    config = Config()
    config.tasks.remote_workers.append(RemoteWorkerConfig("worker", queues=["UNARCHIVE"]))

    event_bus = EventBusService(LocalEventBus())
    executor = RemoteWorkerExecutor(event_bus=event_bus, config=config)

    events = []

    async def event_listener(event: Event) -> None:
        events.append(event)
        command = WorkerTaskCommand.model_validate(event.payload)
        result = WorkerTaskResult(task_id=command.task_id, task_result=TaskResult(success=True, message="OK"))

        result_event = Event(
            type=EventType.WORKER_TASK_ENDED,
            payload=result,
            permissions=PermissionInfo(public_mode=PublicMode.NONE),
        )
        event_bus.push(result_event)

    event_bus.add_queue_consumer(event_listener, "UNARCHIVE")

    def start_task():
        executor.execute_remote_task(
            task_type=TaskType.UNARCHIVE, task_queue="UNARCHIVE", task_args={"src": "src", "dest": "dest"}
        )

    thread = Thread(target=start_task)
    thread.start()
    thread.join()
    assert len(events) == 1
