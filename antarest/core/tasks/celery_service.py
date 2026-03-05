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
CeleryTaskService: dispatches task execution to Celery workers.

Tasks are described by a TaskActionDescriptor (action_type + params) and
sent to the ``task_actions`` queue. A Celery worker picks up the message,
looks up the handler in TaskActionRegistry, and runs it with the full
service stack from MaintenanceContext.
"""

from __future__ import annotations

import logging
import time
from typing import TYPE_CHECKING, Dict, List, Optional, Sequence

from celery.result import AsyncResult
from sqlalchemy import select
from typing_extensions import override

from antarest.core.config import Config
from antarest.core.interfaces.eventbus import Event, EventType, IEventBus
from antarest.core.model import PermissionInfo
from antarest.core.requests import UserHasNotPermissionError
from antarest.core.tasks.action import TaskActionDescriptor
from antarest.core.tasks.model import (
    CustomTaskEventMessages,
    TaskDTO,
    TaskEventPayload,
    TaskJob,
    TaskListFilter,
    TaskStatus,
    TaskType,
)
from antarest.core.tasks.repository import TaskJobRepository
from antarest.core.tasks.service import (
    DEFAULT_AWAIT_MAX_TIMEOUT,
    ITaskService,
    TaskNotFoundError,
    TaskServiceListener,
)
from antarest.core.utils.fastapi_sqlalchemy import db
from antarest.login.utils import require_current_user

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)

TASK_ACTIONS_QUEUE = "task_actions"


class CeleryTaskService(ITaskService):
    """ITaskService implementation that delegates execution to Celery workers."""

    def __init__(
        self,
        config: Config,
        repository: TaskJobRepository,
        event_bus: IEventBus,
        listeners: Sequence[TaskServiceListener] | None = None,
    ):
        self.config = config
        self.repo = repository
        self.event_bus = event_bus
        self._listeners = list(listeners) if listeners else []
        self._celery_tasks: Dict[str, str] = {}  # task_id -> celery_task_id

    @override
    def add_task(
        self,
        action: TaskActionDescriptor,
        name: Optional[str],
        task_type: TaskType,
        ref_id: Optional[str],
        progress: Optional[int],
        custom_event_messages: Optional[CustomTaskEventMessages],
    ) -> str:
        user = require_current_user()

        task = self.repo.save(
            TaskJob(
                name=name or "Unnamed",
                owner_id=user.impersonator,
                type=task_type,
                ref_id=ref_id,
                progress=progress,
            )
        )

        self.event_bus.push(
            Event(
                type=EventType.TASK_ADDED,
                payload=TaskEventPayload(
                    id=task.id,
                    message=(
                        custom_event_messages.start if custom_event_messages is not None else f"Task {task.id} added"
                    ),
                    type=task.type,
                    study_id=task.ref_id,
                ).model_dump(),
                permissions=PermissionInfo(owner=user.impersonator),
            )
        )

        for listener in self._listeners:
            listener.on_task_submit(task.id, task_type=task.get_type())

        # Import here to avoid circular imports at module level
        from antarest.core.tasks.celery_task import run_task_action

        async_result: AsyncResult = run_task_action.apply_async(  # type: ignore
            kwargs={
                "task_id": task.id,
                "action_type": action.action_type,
                "params": action.params,
                "user_id": user.impersonator,
                "task_type": task_type.value,
                "custom_event_messages": custom_event_messages.model_dump() if custom_event_messages else None,
            },
            queue=TASK_ACTIONS_QUEUE,
        )
        self._celery_tasks[task.id] = async_result.id

        return str(task.id)

    @override
    def status_task(
        self,
        task_id: str,
        with_logs: bool = False,
    ) -> TaskDTO:
        if task := self.repo.get(task_id):
            return task.to_dto(with_logs)
        else:
            raise TaskNotFoundError(detail=f"Failed to retrieve task {task_id} in db")

    @override
    def list_tasks(self, task_filter: TaskListFilter) -> List[TaskDTO]:
        current_user = require_current_user()
        user = None if current_user.is_site_admin() else current_user.impersonator
        return [task.to_dto() for task in self.repo.list(task_filter, user)]

    @override
    def await_task(self, task_id: str, timeout_sec: int = DEFAULT_AWAIT_MAX_TIMEOUT) -> None:
        logger.warning(f"Task '{task_id}' dispatched to Celery, will poll for task completion from db")
        end = time.time() + timeout_sec
        while time.time() < end:
            task_status = db.session.execute(select(TaskJob.status).where(TaskJob.id == task_id)).scalar()
            if task_status is None:
                logger.error(f"Awaited task '{task_id}' was not found")
                return
            if TaskStatus(task_status).is_final():
                return
            logger.info("Sleeping 2 seconds...")
            time.sleep(2)
        error_msg = f"Timeout while awaiting task '{task_id}'"
        logger.warning(error_msg)
        raise TimeoutError(error_msg)

    def cancel_task(self, task_id: str) -> None:
        task = self.repo.get_or_raise(task_id)
        user = require_current_user()
        if not (user.is_site_admin() or task.owner_id == user.impersonator):
            raise UserHasNotPermissionError()

        celery_task_id = self._celery_tasks.get(task_id)
        if celery_task_id:
            from antarest.maintenance.app import celery_app

            celery_app.control.revoke(celery_task_id, terminate=True)
            logger.info(f"Revoked Celery task {celery_task_id} for task {task_id}")

        task.status = TaskStatus.CANCELLED.value
        self.repo.save(task)
        for listener in self._listeners:
            listener.on_task_cancel(task.id, task.get_type())

    @override
    def delete_task_by_creation_date(self, task_retention_duration: int) -> int:
        return self.repo.delete_by_creation_date(task_retention_duration=task_retention_duration)
