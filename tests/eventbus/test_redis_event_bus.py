import dataclasses
import json
from unittest.mock import Mock

from antarest.core.interfaces.eventbus import Event, EventType
from antarest.eventbus.business.redis_eventbus import (
    RedisEventBus,
)


def test_lifecycle():
    redis_client = Mock()
    pubsub_mock = Mock()
    redis_client.pubsub.return_value = pubsub_mock
    eventbus = RedisEventBus(redis_client)
    pubsub_mock.subscribe.assert_called_once_with("events")

    event = Event(type=EventType.STUDY_EDITED, payload="foo")
    serialized = event.json()
    pubsub_mock.get_message.return_value = {"data": serialized}
    eventbus.push_event(event)
    redis_client.publish.assert_called_once_with("events", serialized)
    assert eventbus.get_events() == [event]
