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
from abc import abstractmethod
from concurrent.futures import Future, ThreadPoolExecutor
from typing import Any, Dict, List, Union

from typing_extensions import override

from antarest.core.interfaces.eventbus import Event, EventType, IEventBus
from antarest.core.interfaces.service import IService
from antarest.core.model import PermissionInfo, PublicMode
from antarest.core.serde import AntaresBaseModel
from antarest.core.tasks.model import TaskResult

logger = logging.getLogger(__name__)

MAX_WORKERS = 10


class WorkerTaskResult(AntaresBaseModel):
    task_id: str
    task_result: TaskResult


class WorkerTaskCommand(AntaresBaseModel):
    task_id: str
    task_type: str
    task_args: Dict[str, Union[int, float, bool, str]]


class _WorkerTaskEndedCallback:
    """
    Callback function which uses the event bus to notify
    that the worker task is completed (or cancelled).
    """

    def __init__(
        self,
        event_bus: IEventBus,
        task_id: str,
    ) -> None:
        self._event_bus = event_bus
        self._task_id = task_id

    # NOTE: it seems that mypy has an issue with `concurrent.futures.Future`,
    # for this reason we have annotated the `future` parameter with a string.
    def __call__(self, future: "Future[Any]") -> None:
        result = future.result()
        event = Event(
            type=EventType.WORKER_TASK_ENDED,
            payload=WorkerTaskResult(task_id=self._task_id, task_result=result),
            # Use `NONE` for internal events
            permissions=PermissionInfo(public_mode=PublicMode.NONE),
        )
        self._event_bus.push(event)


# fixme: `AbstractWorker` should not inherit from `IService`
class AbstractWorker(IService):
    """
    Base class for workers which listens and process events.

    The worker listens for task command events on specified queues,
    and processes them with the implementation defined `_execute_task`.
    """

    def __init__(
        self,
        name: str,
        event_bus: IEventBus,
        accept: List[str],
    ) -> None:
        """
        Initializes a worker.

        Args:
            name:      Name of this worker
            event_bus: Event bus used for receiving commands,
                       and sending back processing events.
            accept:    The list of queues from which the worker
                       should consume task commands.
        """
        super().__init__()
        self.name = name
        self.event_bus = event_bus
        self.accept = accept
        self.threadpool = ThreadPoolExecutor(
            max_workers=MAX_WORKERS,
            thread_name_prefix="worker_task_",
        )

    @override
    def _loop(self) -> None:
        for task_type in self.accept:
            self.event_bus.add_queue_consumer(self._listen_for_tasks, task_type)

        # All the work is actually performed by callbacks
        # on events.
        # However, we want to keep the service alive while
        # it waits for new events, so infinite loop ...
        while True:
            time.sleep(1)

    async def _listen_for_tasks(self, event: Event) -> None:
        logger.info(f"Accepting new task {event.model_dump_json()}")
        task_info = WorkerTaskCommand.model_validate(event.payload)
        self.event_bus.push(
            Event(
                type=EventType.WORKER_TASK_STARTED,
                payload=task_info,  # Use `NONE` for internal events
                permissions=PermissionInfo(public_mode=PublicMode.NONE),
            )
        )

        future = self.threadpool.submit(self._safe_execute_task, task_info)
        callback = _WorkerTaskEndedCallback(self.event_bus, task_info.task_id)
        future.add_done_callback(callback)

    def _safe_execute_task(self, task_info: WorkerTaskCommand) -> TaskResult:
        try:
            return self._execute_task(task_info)
        except Exception as e:
            logger.error(
                f"Unexpected error occurred when executing task {task_info.model_dump_json()}",
                exc_info=e,
            )
            return TaskResult(success=False, message=repr(e))

    @abstractmethod
    def _execute_task(self, task_info: WorkerTaskCommand) -> TaskResult:
        raise NotImplementedError()
