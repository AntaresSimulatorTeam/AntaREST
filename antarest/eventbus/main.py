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

from antarest.core.interfaces.eventbus import Event
from antarest.core.serde.json import to_json_string
from antarest.eventbus.business.local_eventbus import LocalEventBus
from antarest.eventbus.business.redis_eventbus import RedisEventBus
from antarest.eventbus.service import EventBusService
from antarest.eventbus.web import ConnectionManager


def build_eventbus(
    connection_manager: ConnectionManager,
    autostart: bool = True,
    redis_client: Optional[Redis] = None,  # type: ignore
) -> EventBusService:
    eventbus = EventBusService(
        RedisEventBus(redis_client) if redis_client is not None else LocalEventBus(),
        autostart,
    )

    async def send_event_to_ws(event: Event) -> None:
        event_data = event.model_dump()
        del event_data["permissions"]
        del event_data["channel"]
        await connection_manager.broadcast(to_json_string(event_data), event.permissions, event.channel)

    eventbus.add_listener(send_event_to_ws)

    return eventbus
