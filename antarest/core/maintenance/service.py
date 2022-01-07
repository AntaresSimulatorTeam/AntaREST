import logging

from fastapi import HTTPException

from antarest.core.config import Config
from antarest.core.configdata.model import ConfigData
from antarest.core.interfaces.cache import ICache
from antarest.core.interfaces.eventbus import (
    IEventBus,
)
from antarest.core.maintenance.model import (
    MaintenanceDTO,
    MaintenanceMode,
)
from antarest.core.maintenance.repository import MaintenanceRepository
from antarest.core.requests import (
    RequestParameters,
    MustBeAuthenticatedError,
    UserHasNotPermissionError,
)

logger = logging.getLogger(__name__)


class MaintenanceService:
    def __init__(
        self,
        config: Config,
        repository: MaintenanceRepository,
        event_bus: IEventBus,
        cache: ICache,
    ):
        self.config = config
        self.repo = repository
        self.event_bus = event_bus
        self.cache = cache

    def set_maintenance_status(
        self,
        data: MaintenanceDTO,
        request_params: RequestParameters,
    ) -> None:

        if not request_params.user or not request_params.user.is_site_admin():
            raise UserHasNotPermissionError()

        if data.mode != MaintenanceMode.NORMAL and not data.message:
            raise HTTPException(
                status_code=400, detail="Maintenance message needed"
            )

        # Update cache

        # Update database
        self.repo.save_maintenance_status(data)

        # Send event
        # self.event_bus.push(
        #    Event(
        #        type=EventType.TASK_ADDED,
        #        payload=TaskEventPayload(
        #            id=task.id, message=custom_event_messages.start
        #        ).dict()

    def get_maintenance_status(
        self, request_params: RequestParameters
    ) -> MaintenanceDTO:

        if not request_params.user:
            raise MustBeAuthenticatedError()

        # If element in cache get else get from database and update cache
        print("----------------------------- OK MAN")
        maintenance = self.repo.get_maintenance_status()
        if not maintenance:
            raise HTTPException(
                status_code=400, detail="Maintenance status not found"
            )
        return maintenance
        # return MaintenanceDTO(mode=MaintenanceMode.NORMAL, message="Yo gotti")
