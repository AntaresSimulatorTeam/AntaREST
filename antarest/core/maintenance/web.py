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

import logging
from typing import Any

from fastapi import APIRouter, Body

from antarest.core.config import Config
from antarest.core.maintenance.service import MaintenanceService

logger = logging.getLogger(__name__)


def create_maintenance_api(service: MaintenanceService, config: Config) -> APIRouter:
    """
    Endpoints login implementation
    Args:
        service: login facade service
        config: server config

    Returns:

    """
    bp = APIRouter(prefix="/v1")

    @bp.get("/core/maintenance", include_in_schema=False)
    def get_maintenance_status() -> bool:
        return service.get_maintenance_status()

    @bp.post("/core/maintenance", include_in_schema=False)
    def set_maintenance_status(maintenance: bool) -> Any:
        return service.set_maintenance_status(maintenance)

    @bp.get("/core/maintenance/message", include_in_schema=False)
    def get_message_info() -> str:
        return service.get_message_info()

    @bp.post("/core/maintenance/message", include_in_schema=False)
    def set_message_info(message: str = Body(default="")) -> Any:
        return service.set_message_info(message)

    return bp
