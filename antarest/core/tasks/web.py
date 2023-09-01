import logging
from typing import Any, List

from fastapi import APIRouter, Depends

from antarest.core.config import Config
from antarest.core.jwt import JWTUser
from antarest.core.requests import RequestParameters
from antarest.core.tasks.model import TaskJobLog, TaskListFilter
from antarest.core.tasks.service import TaskJobService
from antarest.core.utils.web import APITag
from antarest.login.auth import Auth

logger = logging.getLogger(__name__)


def create_tasks_api(service: TaskJobService, config: Config) -> APIRouter:
    """
    Endpoints login implementation
    Args:
        service: login facade service
        config: server config
        jwt: jwt manager

    Returns:

    """
    bp = APIRouter(prefix="/v1")
    auth = Auth(config)

    @bp.post("/tasks", tags=[APITag.tasks])
    def list_tasks(
        filter: TaskListFilter,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> Any:
        request_params = RequestParameters(user=current_user)
        return service.list_tasks(filter, request_params)

    @bp.get("/tasks/{task_id}", tags=[APITag.tasks])
    def get_task(
        task_id: str,
        wait_for_completion: bool = False,
        with_logs: bool = False,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> Any:
        request_params = RequestParameters(user=current_user)
        task_status = service.status_task(task_id, request_params, with_logs)
        if wait_for_completion and not task_status.status.is_final():
            service.await_task(task_id)
        return service.status_task(task_id, request_params, with_logs)

    @bp.put("/tasks/{task_id}/cancel", tags=[APITag.tasks])
    def cancel_task(
        task_id: str,
        current_user: JWTUser = Depends(auth.get_current_user),
    ) -> Any:
        request_params = RequestParameters(user=current_user)
        return service.cancel_task(task_id, request_params, dispatch=True)

    return bp
