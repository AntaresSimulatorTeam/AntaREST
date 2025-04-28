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

import concurrent.futures
import http
import logging
from typing import Any, Optional

from fastapi import APIRouter, HTTPException

from antarest.core.config import Config
from antarest.core.tasks.model import TaskDTO, TaskListFilter
from antarest.core.tasks.service import DEFAULT_AWAIT_MAX_TIMEOUT, TaskJobService
from antarest.core.utils.utils import sanitize_uuid
from antarest.core.utils.web import APITag
from antarest.login.auth import Auth

logger = logging.getLogger(__name__)


def create_tasks_api(service: TaskJobService, config: Config) -> APIRouter:
    """
    Endpoints login implementation

    Args:
        service: login facade service
        config: server config

    Returns:
        API router
    """
    auth = Auth(config)
    bp = APIRouter(prefix="/v1", dependencies=[auth.required()])

    @bp.post("/tasks", tags=[APITag.tasks])
    def list_tasks(filter: TaskListFilter) -> Any:
        return service.list_tasks(filter)

    @bp.get("/tasks/{task_id}", tags=[APITag.tasks], response_model=TaskDTO)
    def get_task(
        task_id: str,
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
        sanitized_task_id = sanitize_uuid(task_id)

        task_status = service.status_task(sanitized_task_id, with_logs)

        if wait_for_completion and not task_status.status.is_final():
            # Ensure 0 <= timeout <= 48 h
            timeout = min(max(0, timeout), DEFAULT_AWAIT_MAX_TIMEOUT)
            try:
                service.await_task(sanitized_task_id, timeout_sec=timeout)
            except concurrent.futures.TimeoutError as exc:  # pragma: no cover
                # Note that if the task does not complete within the specified time,
                # the task will continue running but the user will receive a timeout.
                # In this case, it is the user's responsibility to cancel the task.
                raise HTTPException(
                    status_code=http.HTTPStatus.REQUEST_TIMEOUT,
                    detail="The request timed out while waiting for task completion.",
                ) from exc

        return service.status_task(sanitized_task_id, with_logs)

    @bp.put("/tasks/{task_id}/cancel", tags=[APITag.tasks])
    def cancel_task(task_id: str) -> Any:
        return service.cancel_task(task_id, dispatch=True)

    @bp.get(
        "/tasks/{task_id}/progress",
        tags=[APITag.tasks],
        summary="Retrieve task progress from task id",
        response_model=Optional[int],
    )
    def get_progress(task_id: str) -> Optional[int]:
        sanitized_task_id = sanitize_uuid(task_id)
        logger.info(f"Fetching task progress of task {sanitized_task_id}")
        return service.get_task_progress(sanitized_task_id)

    return bp
