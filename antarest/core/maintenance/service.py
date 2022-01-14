import logging
from typing import Optional, Callable

from fastapi import HTTPException

from antarest.core.config import Config
from antarest.core.configdata.model import ConfigDataAppKeys
from antarest.core.interfaces.cache import ICache
from antarest.core.interfaces.eventbus import (
    IEventBus,
    EventType,
    Event,
)
from antarest.core.maintenance.model import (
    MaintenanceMode,
)
from antarest.core.maintenance.repository import MaintenanceRepository
from antarest.core.model import PermissionInfo, PublicMode
from antarest.core.requests import (
    RequestParameters,
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

    def _get_maintenance_data(
        self,
        cache_id: str,
        db_call: Callable[[None], Optional[str]],
        default_value: str,
    ) -> str:

        try:
            data_json = self.cache.get(cache_id)
            if data_json is not None and "content" in data_json.keys():
                return str(data_json["content"])
        except Exception as e:
            logger.error(
                f"Failed to retrieve cache key {cache_id}", exc_info=e
            )

        data: Optional[str] = None
        try:
            data = db_call()
        except Exception as e:
            logger.error(
                f"Failed to fetch {cache_id} from database", exc_info=e
            )

        if not data:
            data = default_value
            logger.error(f"{cache_id} is None in database")

        try:
            self.cache.put(cache_id, {"content": data})
        except Exception as e:
            logger.error(f"Failed to put {cache_id} in cache", exc_info=e)
        return data

    def _set_maintenance_data(
        self,
        data: str,
        cache_id: str,
        db_call: Callable[[int, str], None],
        request_params: RequestParameters,
    ) -> None:

        if not request_params.user or not request_params.user.is_site_admin():
            raise UserHasNotPermissionError()

        try:
            db_call(data)
        except Exception as e:
            logger.error(f"Failed to save {cache_id} in database", exc_info=e)

        try:
            self.cache.put(cache_id, {"content": data})
        except Exception as e:
            cache_save_error = f"Failed to put {cache_id} in cache"
            logger.error(cache_save_error, exc_info=e)
            raise HTTPException(status_code=400, detail=cache_save_error)

    def set_maintenance_status(
        self,
        data: bool,
        request_params: RequestParameters,
    ) -> None:
        maintenance_mode = MaintenanceMode.to_str(data)
        self._set_maintenance_data(
            data=maintenance_mode,
            cache_id=ConfigDataAppKeys.MAINTENANCE_MODE.value,
            db_call=lambda x: self.repo.save_maintenance_mode(x),
            request_params=request_params,
        )
        self.event_bus.push(
            Event(
                type=EventType.MAINTENANCE_MODE,
                payload=data,
                permissions=PermissionInfo(public_mode=PublicMode.READ),
            )
        )

    def get_maintenance_status(self) -> bool:
        data = self._get_maintenance_data(
            cache_id=ConfigDataAppKeys.MAINTENANCE_MODE.value,
            db_call=lambda: self.repo.get_maintenance_mode(),
            default_value=MaintenanceMode.NORMAL_MODE.value,
        )
        return data == MaintenanceMode.MAINTENANCE_MODE.value

    def set_message_info(
        self,
        data: str,
        request_params: RequestParameters,
    ) -> None:
        message = "" if data.replace("\t", "").replace(" ", "") == "" else data
        message = message.strip()
        self._set_maintenance_data(
            data=message,
            cache_id=ConfigDataAppKeys.MESSAGE_INFO.value,
            db_call=lambda x: self.repo.save_message_info(x),
            request_params=request_params,
        )
        self.event_bus.push(
            Event(
                type=EventType.MESSAGE_INFO,
                payload=message,
                permissions=PermissionInfo(public_mode=PublicMode.READ),
            )
        )

    def get_message_info(self) -> str:
        return self._get_maintenance_data(
            cache_id=ConfigDataAppKeys.MESSAGE_INFO.value,
            db_call=lambda: self.repo.get_message_info(),
            default_value="",
        )
