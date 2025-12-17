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

import logging
import time
import uuid
from abc import ABC, abstractmethod
from typing import Awaitable, Callable, List

from typing_extensions import override

from antarest.core.config import Config
from antarest.core.interfaces.eventbus import Event, EventType, IEventBus
from antarest.core.model import PermissionInfo, PublicMode
from antarest.core.tasks.model import TaskResult
from antarest.worker.worker import WorkerTaskCommand, WorkerTaskResult

logger = logging.getLogger(__name__)


class IRemoteExecutor(ABC):
    """
    In charge of remotely executing some particular tasks.

    The API is synchronous, you may embed it inside a task of the task service
    if you need asynchronous behaviour.

    Uses some task models for legacy reasons.
    """

    @abstractmethod
    def execute_remote_task(
        self,
        task_queue: str,
        task_args: dict[str, int | float | bool | str],
    ) -> TaskResult:
        raise NotImplementedError()


class RemoteWorkerExecutor(IRemoteExecutor):
    """
    Implementation which relies on messages exchanged through the event bus with a remote worker.
    """

    def __init__(self, event_bus: IEventBus, config: Config):
        self.event_bus = event_bus
        self.remote_workers = config.tasks.remote_workers

    def _check_remote_worker_for_queue(self, task_queue: str) -> bool:
        return any(task_queue in rw.queues for rw in self.remote_workers)

    @override
    def execute_remote_task(
        self,
        task_queue: str,
        task_args: dict[str, int | float | bool | str],
    ) -> TaskResult:
        if not self._check_remote_worker_for_queue(task_queue):
            raise ValueError(f"No remote worker found for queue {task_queue}")

        remote_task_id = str(uuid.uuid4())

        task_result_wrapper: List[TaskResult] = []

        def _create_awaiter(
            res_wrapper: List[TaskResult],
        ) -> Callable[[Event], Awaitable[None]]:
            async def _await_task_end(event: Event) -> None:
                task_event = WorkerTaskResult.model_validate(event.payload)
                if task_event.task_id == remote_task_id:
                    res_wrapper.append(task_event.task_result)

            return _await_task_end

        listener_id = self.event_bus.add_listener(
            _create_awaiter(task_result_wrapper),
            [EventType.WORKER_TASK_ENDED],
        )
        try:
            self.event_bus.queue(
                Event(
                    type=EventType.WORKER_TASK,
                    payload=WorkerTaskCommand(
                        task_id=remote_task_id,
                        task_type=task_queue,
                        task_args=task_args,
                    ),
                    # Use `NONE` for internal events
                    permissions=PermissionInfo(public_mode=PublicMode.NONE),
                ),
                task_queue,
            )
            while not task_result_wrapper:
                logger.info("💤 Sleeping 1 second...")
                time.sleep(1)
            return task_result_wrapper[0]
        finally:
            self.event_bus.remove_listener(listener_id)
