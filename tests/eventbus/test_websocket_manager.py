from unittest import IsolatedAsyncioTestCase
from unittest.mock import MagicMock

from antarest.core.jwt import JWTUser
from antarest.core.model import PermissionInfo
from antarest.eventbus.web import (
    ConnectionManager,
    WebsocketMessage,
    WebsocketMessageAction,
)
from starlette.websockets import WebSocket


class AsyncMock(MagicMock):
    async def __call__(self, *args, **kwargs):
        return super(AsyncMock, self).__call__(*args, **kwargs)


class ConnectionManagerTest(IsolatedAsyncioTestCase):
    # noinspection PyMethodMayBeStatic
    async def test_subscriptions(self):
        ws_manager = ConnectionManager()

        user = JWTUser(id=1, type="user", impersonator=1, groups=[])
        subscribe_message = WebsocketMessage(
            action=WebsocketMessageAction.SUBSCRIBE, payload="foo"
        )
        unsubscribe_message = WebsocketMessage(
            action=WebsocketMessageAction.UNSUBSCRIBE, payload="foo"
        )
        mock_connection = AsyncMock(spec=WebSocket)
        await ws_manager.connect(mock_connection, user)
        assert len(ws_manager.active_connections) == 1

        ws_manager.process_message(
            subscribe_message.json(), mock_connection, user
        )
        assert len(ws_manager.active_connections[0].channel_subscriptions) == 1
        assert (
            ws_manager.active_connections[0].channel_subscriptions[0] == "foo"
        )

        await ws_manager.broadcast("hello", PermissionInfo(), channel="foo")
        mock_connection.send_text.assert_called_with("hello")

        ws_manager.process_message(
            unsubscribe_message.json(), mock_connection, user
        )
        assert len(ws_manager.active_connections[0].channel_subscriptions) == 0

        ws_manager.disconnect(mock_connection)
        assert len(ws_manager.active_connections) == 0
