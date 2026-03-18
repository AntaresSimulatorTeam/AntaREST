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

import logging
from typing import Annotated

from dishka.integrations.fastapi import DishkaRoute
from fastapi import APIRouter, Body, Depends

from antarest.dependencies import MaintenanceServiceDep, auth_required

logger = logging.getLogger(__name__)


def create_maintenance_api() -> APIRouter:
    bp = APIRouter(prefix="/v1", route_class=DishkaRoute)

    @bp.get("/core/maintenance", include_in_schema=False)
    def get_maintenance_status(service: MaintenanceServiceDep) -> bool:
        return service.get_maintenance_status()

    @bp.post("/core/maintenance", include_in_schema=False, dependencies=[Depends(auth_required)])
    def set_maintenance_status(
        service: MaintenanceServiceDep,
        maintenance: bool,
    ) -> None:
        return service.set_maintenance_status(maintenance)

    @bp.get("/core/maintenance/message", include_in_schema=False)
    def get_message_info(service: MaintenanceServiceDep) -> str:
        return service.get_message_info()

    @bp.post("/core/maintenance/message", include_in_schema=False, dependencies=[Depends(auth_required)])
    def set_message_info(
        service: MaintenanceServiceDep,
        message: Annotated[str, Body()] = "",
    ) -> None:
        return service.set_message_info(message)

    return bp
