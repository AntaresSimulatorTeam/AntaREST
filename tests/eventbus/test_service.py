import time
from datetime import datetime, timedelta
from typing import Callable

import pytest
import redis

from antarest.common.config import Config
from antarest.common.interfaces.eventbus import Event
from antarest.eventbus.main import build_eventbus


def autoretry(func: Callable[..., bool], timeout: int) -> None:
    threshold = datetime.now() + timedelta(seconds=timeout)
    while datetime.now() < threshold:
        if func():
            return
        time.sleep(0.2)
    raise AssertionError()


def test_service_factory():
    config = Config()
    event_bus = build_eventbus(config, autostart=False)
    assert event_bus.backend.__class__.__name__ == "LocalEventBus"
    config = Config({"eventbus": {"redis": {"host": "localhost"}}})
    with pytest.raises(redis.exceptions.ConnectionError):
        # this error implies that this is the redis one...
        build_eventbus(config, autostart=False)


def test_lifecycle():
    event_bus = build_eventbus(Config(), autostart=True)
    test_bucket = []
    lid = event_bus.add_listener(lambda event: test_bucket.append(event))
    event = Event("test", "foo")
    event_bus.push(event)
    autoretry(lambda: len(test_bucket) == 1, 2)

    event_bus.remove_listener(lid)
    test_bucket.clear()
    event_bus.push(event)
    autoretry(lambda: len(test_bucket) == 0, 2)
