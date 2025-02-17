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

from redis import Redis

from antarest.core.application import AppBuildContext
from antarest.core.config import Config
from antarest.eventbus.business.local_eventbus import LocalEventBus
from antarest.eventbus.business.redis_eventbus import RedisEventBus
from antarest.eventbus.service import EventBusService
from antarest.eventbus.web import configure_websockets


def build_eventbus(
    app_ctxt: Optional[AppBuildContext],
    config: Config,
    autostart: bool = True,
    redis_client: Optional[Redis] = None,  # type: ignore
) -> EventBusService:
    eventbus = EventBusService(
        RedisEventBus(redis_client) if redis_client is not None else LocalEventBus(),
        autostart,
    )

    if app_ctxt:
        configure_websockets(app_ctxt, config, eventbus)
    return eventbus
