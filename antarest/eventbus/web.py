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

import dataclasses
import logging
from enum import StrEnum
from http import HTTPStatus
from typing import List, Optional

from fastapi import Depends, HTTPException, Query
from starlette.websockets import WebSocket, WebSocketDisconnect

from antarest.core.application import AppBuildContext
from antarest.core.config import Config
from antarest.core.interfaces.eventbus import Event, IEventBus
from antarest.core.jwt import DEFAULT_ADMIN_USER, JWTUser
from antarest.core.model import PermissionInfo, StudyPermissionType
from antarest.core.permissions import check_permission
from antarest.core.serialization import AntaresBaseModel, to_json_string
from antarest.fastapi_jwt_auth import AuthJWT
from antarest.login.auth import Auth

logger = logging.getLogger(__name__)


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
    channel_subscriptions: List[str] = dataclasses.field(default_factory=list)


class ConnectionManager:
    def __init__(self) -> None:
        self.active_connections: List[WebsocketConnection] = []

    async def connect(self, websocket: WebSocket, user: JWTUser) -> None:
        await websocket.accept()
        self.active_connections.append((WebsocketConnection(websocket, user)))

    def _get_connection(self, websocket: WebSocket) -> Optional[WebsocketConnection]:
        for connection in self.active_connections:
            if connection.websocket == websocket:
                return connection
        logger.warning(f"Failed to remove websocket connection f{websocket}. Not found in active connections.")
        return None

    def disconnect(self, websocket: WebSocket) -> None:
        connection_to_remove: Optional[WebsocketConnection] = self._get_connection(websocket)
        if connection_to_remove is not None:
            self.active_connections.remove(connection_to_remove)

    def process_message(self, message: str, websocket: WebSocket) -> None:
        connection = self._get_connection(websocket)
        if not connection:
            return

        ws_message = WebsocketMessage.parse_raw(message)
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


def configure_websockets(app_ctxt: AppBuildContext, config: Config, event_bus: IEventBus) -> None:
    manager = ConnectionManager()

    async def send_event_to_ws(event: Event) -> None:
        event_data = event.model_dump()
        del event_data["permissions"]
        del event_data["channel"]
        await manager.broadcast(to_json_string(event_data), event.permissions, event.channel)

    @app_ctxt.api_root.websocket("/ws")
    async def connect(
        websocket: WebSocket,
        token: str = Query(...),
        jwt_manager: AuthJWT = Depends(),
    ) -> None:
        user: Optional[JWTUser] = None
        if not config.security.disabled:
            try:
                if not token:
                    raise HTTPException(status_code=HTTPStatus.UNAUTHORIZED)
                user = Auth.get_user_from_token(token, jwt_manager)
                if user is None:
                    raise HTTPException(status_code=HTTPStatus.UNAUTHORIZED)
            except Exception as e:
                logger.error(
                    "Failed to check token from websocket connexion",
                    exc_info=e,
                )
                raise HTTPException(500, "Failed to check auth")
        await manager.connect(websocket, user or DEFAULT_ADMIN_USER)
        try:
            while True:
                message = await websocket.receive_text()
                try:
                    manager.process_message(message, websocket)
                except Exception as e:
                    logger.error(
                        f"Failed to process websocket message {message}",
                        exc_info=e,
                    )
        except WebSocketDisconnect:
            manager.disconnect(websocket)

    event_bus.add_listener(send_event_to_ws)
