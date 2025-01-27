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

from typing import Optional

from antarest.core.application import AppBuildContext
from antarest.core.config import Config
from antarest.core.interfaces.cache import ICache
from antarest.core.interfaces.eventbus import DummyEventBusService, IEventBus
from antarest.core.maintenance.repository import MaintenanceRepository
from antarest.core.maintenance.service import MaintenanceService
from antarest.core.maintenance.web import create_maintenance_api


def build_maintenance_manager(
    app_ctxt: Optional[AppBuildContext],
    config: Config,
    cache: ICache,
    event_bus: IEventBus = DummyEventBusService(),
) -> MaintenanceService:
    repository = MaintenanceRepository()
    service = MaintenanceService(config, repository, event_bus, cache)

    if app_ctxt:
        app_ctxt.api_root.include_router(create_maintenance_api(service, config))

    return service
