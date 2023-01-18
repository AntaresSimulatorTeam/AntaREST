from unittest import IsolatedAsyncioTestCase
from unittest.mock import MagicMock, call

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
        connections = ws_manager.active_connections[0]
        assert len(connections.channel_subscriptions) == 1
        assert connections.channel_subscriptions[0] == "foo"

        # the event manager must send events if the channel is empty (i.e.: ""),
        await ws_manager.broadcast("msg1", PermissionInfo(), channel="")
        # the event manager must send events if the channel is a subscriber channel
        await ws_manager.broadcast("msg2", PermissionInfo(), channel="foo")
        # the event manager must not send events if the channel does not correspond to any subscriber channel
        await ws_manager.broadcast("msg3", PermissionInfo(), channel="bar")

        mock_connection.send_text.assert_has_calls(
            [call("msg1"), call("msg2")]
        )

        ws_manager.process_message(
            unsubscribe_message.json(), mock_connection, user
        )
        assert len(connections.channel_subscriptions) == 0

        ws_manager.disconnect(mock_connection)
        assert len(ws_manager.active_connections) == 0
