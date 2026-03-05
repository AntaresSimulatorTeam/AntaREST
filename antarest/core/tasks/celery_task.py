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
Generic Celery task for executing task actions on workers.

This task is sent by CeleryTaskService and executed by Celery workers
that have the full service stack via MaintenanceContext.
"""

from __future__ import annotations

import logging
from typing import Any, Optional

from antarest.core.jwt import DEFAULT_ADMIN_USER, JWTUser
from antarest.core.tasks.action import TaskActionDescriptor
from antarest.core.tasks.execution import execute_task
from antarest.core.tasks.model import CustomTaskEventMessages, TaskType
from antarest.login.utils import current_user_context
from antarest.maintenance.app import MaintenanceTask, celery_app

logger = logging.getLogger(__name__)


def _build_jwt_user(user_id: int) -> JWTUser:
    """Build a minimal JWTUser for task execution context.

    In a Celery worker we don't have the full JWT token, but we need
    a user context for the task execution. We use the user_id (impersonator)
    to reconstruct a minimal admin-level JWTUser since tasks always run
    with the permissions of their submitter.
    """
    return JWTUser(
        id=user_id,
        type="users",
        impersonator=user_id,
        groups=DEFAULT_ADMIN_USER.groups,
    )


@celery_app.task(
    base=MaintenanceTask,
    bind=True,
    name="run_task_action",
)
def run_task_action(
    self: MaintenanceTask,
    task_id: str,
    action_type: str,
    params: dict[str, Any],
    user_id: int,
    task_type: str,
    custom_event_messages: Optional[dict[str, str]] = None,
) -> None:
    """Generic Celery task that executes any registered task action.

    Args:
        task_id: The TaskJob ID (already created in DB by CeleryTaskService).
        action_type: Registry key for the action handler.
        params: JSON-serializable parameters for the handler.
        user_id: The impersonator user ID for user context.
        task_type: TaskType value string.
        custom_event_messages: Optional custom event messages dict.
    """
    ctx = self.context
    descriptor = TaskActionDescriptor(action_type=action_type, params=params)
    jwt_user = _build_jwt_user(user_id)

    parsed_messages = CustomTaskEventMessages(**custom_event_messages) if custom_event_messages else None

    with current_user_context(jwt_user):
        execute_task(
            task_id=task_id,
            task_type=TaskType(task_type),
            action=descriptor,
            core_services=ctx.core_services,
            event_bus=ctx.core_services.event_bus,
            repo=ctx.core_services.task_service.repo,  # type: ignore[attr-defined]
            jwt_user=jwt_user,
            custom_event_messages=parsed_messages,
            listeners=[],
        )
