# Copyright (c) 2024, RTE (https://www.rte-france.com)
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

import logging
import shutil
import time
from threading import Thread
from typing import Callable, Optional

from fastapi import HTTPException

from antarest.core.config import Config
from antarest.core.configdata.model import ConfigDataAppKeys
from antarest.core.interfaces.cache import ICache
from antarest.core.interfaces.eventbus import Event, EventType, IEventBus
from antarest.core.maintenance.model import MaintenanceMode
from antarest.core.maintenance.repository import MaintenanceRepository
from antarest.core.model import PermissionInfo, PublicMode
from antarest.core.requests import RequestParameters, UserHasNotPermissionError

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
        self._init()

    def _init(self) -> None:
        self.thread = Thread(
            target=self.check_disk_usage,
            name=self.__class__.__name__,
            daemon=True,
        )
        self.thread.start()

    def check_disk_usage(self) -> None:
        while True:
            for name, workspace in self.config.storage.workspaces.items():
                try:
                    usage = shutil.disk_usage(workspace.path)
                    logger.info(
                        f"Disk usage for {name}: {(100 * usage.used / usage.total):.2f}%"
                        f" ({(usage.free / 1000000000):.3f}GB free)"
                    )
                except Exception as e:
                    logger.error(
                        f"Failed to check disk usage for disk {workspace.path}",
                        exc_info=e,
                    )
            time.sleep(3600)

    def _get_maintenance_data(
        self,
        cache_id: str,
        db_call: Callable[[], Optional[str]],
        default_value: str,
    ) -> str:
        try:
            data_json = self.cache.get(cache_id)
            if data_json is not None and "content" in data_json.keys():
                return str(data_json["content"])
        except Exception as e:
            logger.error(f"Failed to retrieve cache key {cache_id}", exc_info=e)

        data: Optional[str] = None
        try:
            data = db_call()
        except Exception as e:
            logger.error(f"Failed to fetch {cache_id} from database", exc_info=e)

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
        db_call: Callable[[str], None],
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
            raise HTTPException(
                status_code=500,
                detail=cache_save_error,
            ) from e

    def set_maintenance_status(
        self,
        data: bool,
        request_params: RequestParameters,
    ) -> None:
        maintenance_mode = MaintenanceMode.from_bool(data)
        self._set_maintenance_data(
            data=maintenance_mode.value,
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
        return bool(MaintenanceMode(data))

    def set_message_info(
        self,
        data: str,
        request_params: RequestParameters,
    ) -> None:
        message = data.strip()
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
