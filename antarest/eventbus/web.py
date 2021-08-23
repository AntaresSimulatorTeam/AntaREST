import json
import logging
from http import HTTPStatus
from typing import List

import dataclasses
from fastapi import FastAPI, Query, HTTPException, Depends
from fastapi_jwt_auth import AuthJWT  # type: ignore
from starlette.websockets import WebSocket, WebSocketDisconnect

from antarest.core.config import Config
from antarest.core.interfaces.eventbus import IEventBus, Event
from antarest.login.auth import Auth

logger = logging.getLogger(__name__)


class ConnectionManager:
    def __init__(self) -> None:
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket) -> None:
        self.active_connections.remove(websocket)

    async def send_personal_message(
        self, message: str, websocket: WebSocket
    ) -> None:
        await websocket.send_text(message)

    async def broadcast(self, message: str) -> None:
        for connection in self.active_connections:
            await connection.send_text(message)


def configure_websockets(
    application: FastAPI, config: Config, event_bus: IEventBus
) -> None:

    manager = ConnectionManager()

    async def send_event_to_ws(event: Event) -> None:
        # TODO use event permissions to only send to specified rooms
        await manager.broadcast(json.dumps(dataclasses.asdict(event)))

    @application.websocket("/ws")
    async def connect(
        websocket: WebSocket,
        token: str = Query(...),
        jwt_manager: AuthJWT = Depends(),
    ) -> None:
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

        await manager.connect(websocket)
        try:
            while True:
                await websocket.receive_text()

        except WebSocketDisconnect:
            manager.disconnect(websocket)

    event_bus.add_listener(send_event_to_ws)
