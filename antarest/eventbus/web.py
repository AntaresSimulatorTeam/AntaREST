import dataclasses
import json
import logging
from http import HTTPStatus
from typing import List, Dict, Optional, Tuple

from fastapi import FastAPI, Query, HTTPException, Depends
from fastapi_jwt_auth import AuthJWT  # type: ignore
from starlette.websockets import WebSocket, WebSocketDisconnect

from antarest.core.config import Config
from antarest.core.interfaces.eventbus import IEventBus, Event
from antarest.core.jwt import JWTUser, DEFAULT_ADMIN_USER
from antarest.core.model import PermissionInfo, PermissionFullInfo
from antarest.core.permissions import check_permission
from antarest.login.auth import Auth

logger = logging.getLogger(__name__)


class ConnectionManager:
    def __init__(self) -> None:
        self.active_connections: List[Tuple[WebSocket, JWTUser]] = []

    async def connect(self, websocket: WebSocket, user: JWTUser) -> None:
        await websocket.accept()
        self.active_connections.append((websocket, user))

    def disconnect(self, websocket: WebSocket) -> None:
        connexion_to_remove: Optional[Tuple[WebSocket, JWTUser]] = None
        for connection in self.active_connections:
            if connection[0] == websocket:
                connexion_to_remove = connection
                break
        if connexion_to_remove is not None:
            self.active_connections.remove(connexion_to_remove)
        else:
            logger.warning(
                f"Failed to remove websocket connection f{websocket}. Not found in active connections."
            )

    async def send_personal_message(
        self, message: str, websocket: WebSocket
    ) -> None:
        await websocket.send_text(message)

    async def broadcast(
        self, message: str, permissions: PermissionFullInfo
    ) -> None:
        for connection, user in self.active_connections:
            if check_permission(user, permissions, permissions.permission):
                await connection.send_text(message)


def configure_websockets(
    application: FastAPI, config: Config, event_bus: IEventBus
) -> None:

    manager = ConnectionManager()

    async def send_event_to_ws(event: Event) -> None:
        # TODO use event permissions to only send to specified rooms
        event_data = dataclasses.asdict(event)
        del event_data["permissions"]
        await manager.broadcast(json.dumps(event_data), event.permissions)

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
                await websocket.receive_text()

        except WebSocketDisconnect:
            manager.disconnect(websocket)

    event_bus.add_listener(send_event_to_ws)
