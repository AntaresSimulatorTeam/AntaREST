import dataclasses
from flask import Flask
from flask_socketio import SocketIO, join_room  # type: ignore

from antarest.common.interfaces.eventbus import IEventBus, Event
from antarest.login.auth import Auth


def configure_websockets(application: Flask, event_bus: IEventBus) -> None:
    socketio = SocketIO(async_mode="gevent", cors_allowed_origins="*")
    socketio.init_app(application)
    application.socketio = socketio

    def send_event_to_ws(event: Event) -> None:
        socketio.emit("all", dataclasses.asdict(event))

    @socketio.on("connect")
    def test_connect() -> None:
        pass
        # user = Auth.get_current_user()
        # if user is None:
        #     raise ConnectionRefusedError('unauthorized!')

    @socketio.on("disconnect")
    def test_disconnect() -> None:
        print("Client disconnected")

    event_bus.add_listener(send_event_to_ws)
