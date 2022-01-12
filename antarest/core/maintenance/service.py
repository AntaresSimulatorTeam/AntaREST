import logging
from typing import Any, Optional, Callable

from fastapi import HTTPException

from antarest.core.config import Config
from antarest.core.configdata.model import ConfigData, ConfigDataAppKeys
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

    def _get_maintenance_data(
        self,
        cache_id: str,
        db_call: Optional[Callable[[int], Optional[str]]],
        json_key: str,
        cache_get_error: str,
        database_get_error: str,
        database_not_found: str,
        raise_db_not_found: bool,
        cache_set_error: str,
        default_value: str,
        request_params: RequestParameters,
    ):

        if not request_params.user:
            raise MustBeAuthenticatedError()

        # Get maintenance status from cache
        try:
            data_json = self.cache.get(cache_id)
            if data_json is not None and json_key in data_json.keys():
                return data_json[json_key]
        except Exception as e:
            logger.error(cache_get_error, exc_info=e)

        # Else get from database
        data = default_value
        try:
            data = db_call(0)
        except Exception as e:
            logger.error(database_get_error, exc_info=e)

        if not data:
            data = default_value
            if raise_db_not_found:
                raise HTTPException(status_code=400, detail=database_not_found)
            else:
                logger.error(database_not_found)

        # Update cache
        try:
            self.cache.put(cache_id, {json_key: data})
        except Exception as e:
            logger.error(cache_set_error, exc_info=e)
        return data

    def _set_maintenance_data(
        self,
        data: str,
        cache_id: str,
        db_call: Optional[Callable[[int, str], None]],
        json_cache_key: str,
        database_save_error: str,
        cache_save_error: str,
        request_params: RequestParameters,
    ) -> None:

        if not request_params.user or not request_params.user.is_site_admin():
            raise UserHasNotPermissionError()

        # Update database
        try:
            db_call(0, data)
        except Exception as e:
            logger.error(database_save_error, exc_info=e)
            raise HTTPException(status_code=400, detail=database_save_error)

        # Update cache
        try:
            self.cache.put(cache_id, {json_cache_key: data})
        except Exception as e:
            logger.error(cache_save_error, exc_info=e)
            raise HTTPException(status_code=400, detail=cache_save_error)

    # SET MAINTENANCE STATUS
    def set_maintenance_status(
        self,
        data: bool,
        request_params: RequestParameters,
    ) -> None:
        maintenance_mode = MaintenanceMode.to_str(data)
        self._set_maintenance_data(
            data=maintenance_mode,
            cache_id=ConfigDataAppKeys.MAINTENANCE_MODE.value,
            db_call=lambda x, y: self.repo.save_maintenance_mode(x, y),
            json_cache_key="maintenance",
            database_save_error="Maintenance mode not saved in database (Error)",
            cache_save_error="Maintenance mode not saved in cache (Error)",
            request_params=request_params,
        )
        self.event_bus.push(
            Event(
                type=EventType.MAINTENANCE_MODE,
                payload=data,
                permissions=PermissionInfo(public_mode=PublicMode.READ),
            )
        )

    # GET MAINTENANCE STATUS
    def get_maintenance_status(
        self, request_params: RequestParameters
    ) -> bool:
        data = self._get_maintenance_data(
            cache_id=ConfigDataAppKeys.MAINTENANCE_MODE.value,
            db_call=lambda x: self.repo.get_maintenance_mode(x),
            json_key="maintenance",
            cache_get_error="Can't get maintenance mode from cache",
            database_get_error="Error while getting maintenance mode from database",
            database_not_found="Maintenance status not found",
            raise_db_not_found=True,
            cache_set_error="Error while setting maintenance mode in cache",
            default_value=MaintenanceMode.NORMAL_MODE.value,
            request_params=request_params,
        )
        return data == MaintenanceMode.MAINTENANCE_MODE.value

    # SET MESSAGE INFO
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
            db_call=lambda x, y: self.repo.save_message_info(x, y),
            json_cache_key="message",
            database_save_error="Message info not saved in database (Error)",
            cache_save_error="Message info not saved in cache (Error)",
            request_params=request_params,
        )
        self.event_bus.push(
            Event(
                type=EventType.MESSAGE_INFO,
                payload=message,
                permissions=PermissionInfo(
                    owner=request_params.user.impersonator
                ),
            )
        )

    # GET MESSAGE INFO
    def get_message_info(
        self, request_params: RequestParameters
    ) -> MaintenanceMode:
        return self._get_maintenance_data(
            cache_id=ConfigDataAppKeys.MESSAGE_INFO.value,
            db_call=lambda x: self.repo.get_message_info(x),
            json_key="message",
            cache_get_error="Can't get message info from cache",
            database_get_error="Error while getting message info from database",
            database_not_found="Message info not found in database",
            raise_db_not_found=False,
            cache_set_error="Error while setting message info in cache",
            default_value="",
            request_params=request_params,
        )
