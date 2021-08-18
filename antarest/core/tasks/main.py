from fastapi import FastAPI

from antarest.core.config import Config
from antarest.core.interfaces.eventbus import IEventBus, DummyEventBusService
from antarest.core.tasks.service import TaskJobService
from antarest.core.tasks.web import create_tasks_api


def build_taskjob_manager(
    application: FastAPI,
    config: Config,
    event_bus: IEventBus = DummyEventBusService(),
) -> TaskJobService:
    service = TaskJobService(config, event_bus)

    application.include_router(create_tasks_api(service, config))

    return service
