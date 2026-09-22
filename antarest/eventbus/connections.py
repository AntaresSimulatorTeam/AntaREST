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
from __future__ import annotations

import dataclasses
import logging
from enum import StrEnum

from starlette.websockets import WebSocket

from antarest.core.interfaces.eventbus import Event, IEventBus
from antarest.core.jwt import JWTUser
from antarest.core.model import PermissionInfo, StudyPermissionType
from antarest.core.permissions import check_permission
from antarest.core.serde import AntaresBaseModel
from antarest.core.serde.json import to_json_string

logger = logging.getLogger(__name__)


class ConnectionManager:
    def __init__(self) -> None:
        self.active_connections: list[WebsocketConnection] = []

    async def connect(self, websocket: WebSocket, user: JWTUser) -> None:
        await websocket.accept()
        self.active_connections.append(WebsocketConnection(websocket, user))

    def _get_connection(self, websocket: WebSocket) -> WebsocketConnection | None:
        for connection in self.active_connections:
            if connection.websocket == websocket:
                return connection
        logger.warning(f"Failed to remove websocket connection f{websocket}. Not found in active connections.")
        return None

    def disconnect(self, websocket: WebSocket) -> None:
        connection_to_remove: WebsocketConnection | None = self._get_connection(websocket)
        if connection_to_remove is not None:
            self.active_connections.remove(connection_to_remove)

    def process_message(self, message: str, websocket: WebSocket) -> None:
        connection = self._get_connection(websocket)
        if not connection:
            return

        ws_message = WebsocketMessage.model_validate_json(message)
        if ws_message.action == WebsocketMessageAction.SUBSCRIBE:
            if ws_message.payload not in connection.channel_subscriptions:
                connection.channel_subscriptions.append(ws_message.payload)
        elif ws_message.action == WebsocketMessageAction.UNSUBSCRIBE:
            if ws_message.payload in connection.channel_subscriptions:
                connection.channel_subscriptions.remove(ws_message.payload)

    async def broadcast(self, message: str, permissions: PermissionInfo, channel: str) -> None:
        for connection in self.active_connections:
            # if is subscribed to chanel and has permission, send message to websocket
            if (not channel or channel in connection.channel_subscriptions) and check_permission(
                connection.user, permissions, StudyPermissionType.READ
            ):
                await connection.websocket.send_text(message)


def connect_event_bus(event_bus: IEventBus, manager: ConnectionManager) -> None:
    """Wire an event bus to the websocket connection manager."""

    async def send_event_to_ws(event: Event) -> None:
        event_data = event.model_dump()
        del event_data["permissions"]
        del event_data["channel"]
        await manager.broadcast(to_json_string(event_data), event.permissions, event.channel)

    event_bus.add_listener(send_event_to_ws)


class WebsocketMessageAction(StrEnum):
    SUBSCRIBE = "SUBSCRIBE"
    UNSUBSCRIBE = "UNSUBSCRIBE"


class WebsocketMessage(AntaresBaseModel):
    action: WebsocketMessageAction
    payload: str


@dataclasses.dataclass
class WebsocketConnection:
    websocket: WebSocket
    user: JWTUser
    channel_subscriptions: list[str] = dataclasses.field(default_factory=list)
