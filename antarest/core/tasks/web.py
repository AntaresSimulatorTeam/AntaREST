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

import http
import logging
from http import HTTPStatus
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query

from antarest.core.api_types import UuidStr
from antarest.core.tasks.model import TaskDTO, TaskListFilter
from antarest.core.tasks.service import DEFAULT_AWAIT_MAX_TIMEOUT
from antarest.core.utils.web import APITag
from antarest.dependencies import TaskServiceDep, auth_required

logger = logging.getLogger(__name__)


def create_tasks_api() -> APIRouter:
    bp = APIRouter(prefix="/v1", tags=[APITag.tasks], dependencies=[Depends(auth_required)])

    @bp.post("/tasks", deprecated=True)
    def list_tasks(service: TaskServiceDep, filter: TaskListFilter) -> list[TaskDTO]:
        return service.list_tasks(filter)

    @bp.get("/tasks")
    def get_task_list(service: TaskServiceDep, task_filter: Annotated[TaskListFilter, Query()]) -> list[TaskDTO]:
        return service.list_tasks(task_filter)

    @bp.get("/tasks/{task_id}")
    async def get_task(
        service: TaskServiceDep,
        task_id: UuidStr,
        wait_for_completion: bool = False,
        with_logs: bool = False,
        timeout: int = DEFAULT_AWAIT_MAX_TIMEOUT,
    ) -> TaskDTO:
        """
        Retrieve information about a specific task.

        Args:
        - `task_id`: Unique identifier of the task.
        - `wait_for_completion`: Set to `True` to wait for task completion.
        - `with_logs`: Set to `True` to retrieve the job logs (Antares Solver logs).
        - `timeout`: Maximum time in seconds to wait for task completion.

        Raises:
        - 408 REQUEST_TIMEOUT: when the request times out while waiting for task completion.

        Returns:
            TaskDTO: Information about the specified task.
        """
        task_status = service.status_task(task_id, with_logs)

        if wait_for_completion and not task_status.status.is_final():
            # Ensure 0 <= timeout <= 48 h
            timeout = min(max(0, timeout), DEFAULT_AWAIT_MAX_TIMEOUT)
            try:
                # Prefer the async implementation to avoid blocking the event loop.
                await service.await_task_async(task_id, timeout_sec=timeout)
            except TimeoutError as exc:  # pragma: no cover
                # Note that if the task does not complete within the specified time,
                # the task will continue running but the user will receive a timeout.
                # In this case, it is the user's responsibility to cancel the task.
                raise HTTPException(
                    status_code=http.HTTPStatus.REQUEST_TIMEOUT,
                    detail="The request timed out while waiting for task completion.",
                ) from exc

        return service.status_task(task_id, with_logs)

    @bp.put("/tasks/{task_id}/cancel", status_code=HTTPStatus.ACCEPTED)
    def cancel_task(service: TaskServiceDep, task_id: UuidStr) -> None:
        logger.info(f"Requesting cancellation for task {task_id}")
        service.cancel_task(task_id)

    @bp.get(
        "/tasks/{task_id}/progress",
        summary="Retrieve task progress from task id",
    )
    def get_progress(service: TaskServiceDep, task_id: UuidStr) -> int | None:
        logger.info(f"Fetching task progress of task {task_id}")
        return service.get_task_progress(task_id)

    return bp
