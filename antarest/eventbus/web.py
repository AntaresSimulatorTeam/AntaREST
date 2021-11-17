import dataclasses
import json
import logging
from enum import Enum
from http import HTTPStatus
from typing import List, Dict, Optional, Tuple

from fastapi import FastAPI, Query, HTTPException, Depends
from fastapi_jwt_auth import AuthJWT  # type: ignore
from pydantic import BaseModel
from starlette.websockets import WebSocket, WebSocketDisconnect

from antarest.core.config import Config
from antarest.core.interfaces.eventbus import IEventBus, Event
from antarest.core.jwt import JWTUser, DEFAULT_ADMIN_USER
from antarest.core.model import PermissionInfo, StudyPermissionType
from antarest.core.permissions import check_permission
from antarest.login.auth import Auth

logger = logging.getLogger(__name__)


class WebsocketMessageAction(str, Enum):
    SUBSCRIBE = "SUBSCRIBE"
    UNSUBSCRIBE = "UNSUBSCRIBE"


class WebsocketMessage(BaseModel):
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

    def _get_connection(
        self, websocket: WebSocket
    ) -> Optional[WebsocketConnection]:
        for connection in self.active_connections:
            if connection.websocket == websocket:
                return connection
        logger.warning(
            f"Failed to remove websocket connection f{websocket}. Not found in active connections."
        )
        return None

    def disconnect(self, websocket: WebSocket) -> None:
        connection_to_remove: Optional[
            WebsocketConnection
        ] = self._get_connection(websocket)
        if connection_to_remove is not None:
            self.active_connections.remove(connection_to_remove)

    def process_message(
        self, message: str, websocket: WebSocket, user: JWTUser
    ) -> None:
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

    async def broadcast(
        self, message: str, permissions: PermissionInfo, channel: Optional[str]
    ) -> None:
        for connection in self.active_connections:
            if check_permission(
                connection.user, permissions, StudyPermissionType.READ
            ):
                if (
                    channel is None
                    or channel in connection.channel_subscriptions
                ):
                    await connection.websocket.send_text(message)


def configure_websockets(
    application: FastAPI, config: Config, event_bus: IEventBus
) -> None:

    manager = ConnectionManager()

    async def send_event_to_ws(event: Event) -> None:
        event_data = event.dict()
        del event_data["permissions"]
        del event_data["channel"]
        await manager.broadcast(
            json.dumps(event_data), event.permissions, event.channel
        )

    @application.websocket("/ws")
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
                    # TODO check auth and subscribe to rooms
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
                    manager.process_message(
                        message, websocket, user or DEFAULT_ADMIN_USER
                    )
                except Exception as e:
                    logger.error(
                        f"Failed to process websocket message {message}",
                        exc_info=e,
                    )
        except WebSocketDisconnect:
            manager.disconnect(websocket)

    event_bus.add_listener(send_event_to_ws)
