from typing import Optional

from fastapi import FastAPI

from antarest.core.config import Config
from antarest.core.tasks.service import ITaskService
from antarest.scheduler.repository import ScheduledActionsRepository
from antarest.scheduler.service import SchedulerService
from antarest.scheduler.web import create_scheduler_api


def build_scheduler(
    application: Optional[FastAPI],
    config: Config,
    task_service: ITaskService,
    service: Optional[SchedulerService] = None,
) -> SchedulerService:
    """
    Login module linking dependency

    Args:
        application: flask application
        config: server configuration
        task_service: task service
        service: used by testing to inject mock. Let None to use true instantiation

    Returns: user facade service

    """

    if service is None:
        service = SchedulerService(task_service, ScheduledActionsRepository())

    if application:
        application.include_router(create_scheduler_api(service, config))

    return service
