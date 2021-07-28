import json
from unittest.mock import Mock

import dataclasses
import pytest

from antarest.core.config import RedisConfig
from antarest.core.interfaces.eventbus import Event
from antarest.eventbus.business.redis_eventbus import (
    RedisEventBus,
)


def test_lifecycle():
    redis_client = Mock()
    pubsub_mock = Mock()
    redis_client.pubsub.return_value = pubsub_mock
    eventbus = RedisEventBus(RedisConfig(), redis_client)
    pubsub_mock.subscribe.assert_called_once_with("events")

    event = Event("test", "foo")
    serialized = json.dumps(dataclasses.asdict(event))
    pubsub_mock.get_message.return_value = {"data": serialized}
    eventbus.push_event(event)
    redis_client.publish.assert_called_once_with("events", serialized)
    assert eventbus.get_events() == [event]
