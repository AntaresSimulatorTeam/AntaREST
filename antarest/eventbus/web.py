import dataclasses
import logging

from flask import Flask, request
from flask_socketio import SocketIO, join_room, emit  # type: ignore

from antarest.common.config import Config
from antarest.common.interfaces.eventbus import IEventBus, Event
from antarest.login.auth import Auth

logger = logging.getLogger(__name__)


def configure_websockets(
    application: Flask, config: Config, event_bus: IEventBus
) -> None:
    socketio = SocketIO(async_mode="gevent", cors_allowed_origins="*")
    socketio.init_app(application)
    application.socketio = socketio

    def send_event_to_ws(event: Event) -> None:
        # TODO use event permissions to only send to specified rooms
        socketio.emit("all", dataclasses.asdict(event))

    @socketio.on("connect")  # type: ignore
    def test_connect() -> None:
        if not config.security.disable:
            try:
                token = request.event["args"][1]["token"]  # type: ignore
                user = Auth.get_user_from_token(token)
                if user is None:
                    # TODO check auth and subscribe to rooms
                    raise ConnectionRefusedError("unauthorized!")
            except Exception as e:
                logger.error(
                    "Failed to check token from websocket connexion",
                    exc_info=e,
                )
                raise ConnectionRefusedError("Failed to check auth")

    @socketio.on("disconnect")  # type: ignore
    def test_disconnect() -> None:
        print("Client disconnected")

    event_bus.add_listener(send_event_to_ws)
