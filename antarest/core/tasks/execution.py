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
Shared task lifecycle logic used by both TaskJobService and CeleryTaskService.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Optional, Sequence

from sqlalchemy import update

from antarest.core.interfaces.eventbus import Event, EventChannelDirectory, EventType
from antarest.core.logging.utils import task_context
from antarest.core.model import PermissionInfo, PublicMode
from antarest.core.tasks.action import TaskActionDescriptor, TaskActionRegistry
from antarest.core.tasks.model import (
    CustomTaskEventMessages,
    TaskEventPayload,
    TaskJob,
    TaskStatus,
    TaskType,
)
from antarest.core.tasks.service import TaskLogAndProgressRecorder, TaskServiceListener
from antarest.core.utils.fastapi_sqlalchemy import db
from antarest.core.utils.utils import current_time, retry

if TYPE_CHECKING:
    from antarest.core.interfaces.eventbus import IEventBus
    from antarest.core.jwt import JWTUser
    from antarest.core.tasks.repository import TaskJobRepository
    from antarest.service_creator import CoreServices

logger = logging.getLogger(__name__)


def execute_task(
    task_id: str,
    task_type: TaskType,
    action: TaskActionDescriptor,
    core_services: CoreServices,
    event_bus: IEventBus,
    repo: TaskJobRepository,
    jwt_user: JWTUser,
    custom_event_messages: Optional[CustomTaskEventMessages],
    listeners: Sequence[TaskServiceListener],
) -> None:
    """Full task lifecycle: RUNNING -> execute handler -> COMPLETED/FAILED.

    This function is designed to run in a thread (TaskJobService) or in a
    Celery worker. It handles all DB updates, event publishing, and error
    handling.
    """
    with task_context(task_id=task_id, user=jwt_user):
        try:
            status = TaskStatus.FAILED
            for listener in listeners:
                listener.on_task_start(task_id, task_type)

            with db():
                task = retry(lambda: repo.get_or_raise(task_id))
                study_id = task.ref_id

            event_bus.push(
                Event(
                    type=EventType.TASK_RUNNING,
                    payload=TaskEventPayload(
                        id=task_id,
                        message=(
                            custom_event_messages.running
                            if custom_event_messages is not None
                            else f"Task {task_id} is running"
                        ),
                        type=task_type,
                        study_id=study_id,
                    ).model_dump(),
                    permissions=PermissionInfo(public_mode=PublicMode.READ),
                    channel=EventChannelDirectory.TASK + task_id,
                )
            )

            logger.info(f"Starting task {task_id}")
            with db():
                stmt = update(TaskJob).where(TaskJob.id == task_id).values(status=TaskStatus.RUNNING.value)
                db.session.execute(stmt)
                db.session.commit()
            logger.info(f"Task {task_id} set to RUNNING")

            handler = TaskActionRegistry.get_handler(action.action_type)
            with db():
                result = handler(
                    core_services, action.params, TaskLogAndProgressRecorder(task_id, db.session, event_bus)
                )

            status = TaskStatus.COMPLETED if result.success else TaskStatus.FAILED
            logger.info(f"Task {task_id} ended with status {status}")

            with db():
                completion_date = current_time() if status.is_final() else None
                stmt = (
                    update(TaskJob)
                    .where(TaskJob.id == task_id)
                    .values(
                        status=status.value,
                        result_msg=result.message,
                        result_status=result.success,
                        result=result.return_value,
                        completion_date=completion_date,
                    )
                )
                db.session.execute(stmt)
                db.session.commit()

            event_type = {True: EventType.TASK_COMPLETED, False: EventType.TASK_FAILED}[result.success]
            event_msg = {True: "completed", False: "failed"}[result.success]
            event_bus.push(
                Event(
                    type=event_type,
                    payload=TaskEventPayload(
                        id=task_id,
                        message=(
                            custom_event_messages.end
                            if custom_event_messages is not None
                            else f"Task {task_id} {event_msg}"
                        ),
                        type=task_type,
                        study_id=study_id,
                    ).model_dump(),
                    permissions=PermissionInfo(public_mode=PublicMode.READ),
                    channel=EventChannelDirectory.TASK + task_id,
                )
            )
        except Exception as exc:
            err_msg = f"Task {task_id} failed: Unhandled exception {exc}"
            logger.error(err_msg, exc_info=exc)

            try:
                with db():
                    stmt = (
                        update(TaskJob)
                        .where(TaskJob.id == task_id)
                        .values(
                            status=TaskStatus.FAILED.value,
                            result_msg=str(exc),
                            result_status=False,
                            completion_date=current_time(),
                        )
                    )
                    db.session.execute(stmt)
                    db.session.commit()

                message = err_msg if custom_event_messages is None else custom_event_messages.end
                event_bus.push(
                    Event(
                        type=EventType.TASK_FAILED,
                        payload=TaskEventPayload(
                            id=task_id, message=message, type=task_type, study_id=study_id
                        ).model_dump(),
                        permissions=PermissionInfo(public_mode=PublicMode.READ),
                        channel=EventChannelDirectory.TASK + task_id,
                    )
                )
            except Exception as inner_exc:
                logger.error(
                    f"An exception occurred while handling execution error of task {task_id}: {inner_exc}",
                    exc_info=inner_exc,
                )
        finally:
            for listener in listeners:
                listener.on_task_end(task_id, task_type, status)
