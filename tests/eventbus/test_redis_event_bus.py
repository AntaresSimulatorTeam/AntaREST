import json
from unittest.mock import Mock

import dataclasses
import pytest

from antarest.common.interfaces.eventbus import Event
from antarest.eventbus.business.redis_eventbus import (
    parse_config,
    RedisEventBus,
)


def test_conf():
    config = {"host": "localhost", "port": 5555}
    redis_config = parse_config(config)
    assert redis_config.port == 5555
    assert redis_config.host == "localhost"

    config = {"host": "localhost"}
    redis_config = parse_config(config)
    assert redis_config.port == 6379

    config = {}
    with pytest.raises(TypeError):
        parse_config(config)

    config = {"host": "localhost", "foo": "bar"}
    with pytest.raises(TypeError):
        parse_config(config)


def test_lifecycle():
    redis_client = Mock()
    pubsub_mock = Mock()
    redis_client.pubsub.return_value = pubsub_mock
    eventbus = RedisEventBus({"host": "localhost"}, redis_client)
    pubsub_mock.subscribe.assert_called_once_with("events")

    event = Event("test", "foo")
    serialized = json.dumps(dataclasses.asdict(event))
    pubsub_mock.get_message.return_value = {"data": serialized}
    eventbus.push_event(event)
    redis_client.publish.assert_called_once_with("events", serialized)
    assert eventbus.get_events() == [event]
