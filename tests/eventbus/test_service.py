import asyncio
import time
from datetime import datetime, timedelta
from typing import Awaitable, Callable, List
from unittest.mock import MagicMock, Mock

from antarest.core.config import Config, EventBusConfig, RedisConfig
from antarest.core.interfaces.eventbus import Event, EventType
from antarest.core.model import PermissionInfo, PublicMode
from antarest.eventbus.main import build_eventbus
from tests.conftest import autoretry_assert


def test_service_factory():
    config = Config()
    redis_client = Mock()
    event_bus = build_eventbus(MagicMock(), config, autostart=False)
    assert event_bus.backend.__class__.__name__ == "LocalEventBus"
    config = Config(
        redis=RedisConfig(host="localhost"), eventbus=EventBusConfig()
    )

    event_bus = build_eventbus(
        MagicMock(), config, autostart=False, redis_client=redis_client
    )
    assert event_bus.backend.__class__.__name__ == "RedisEventBus"


def test_lifecycle():
    event_bus = build_eventbus(MagicMock(), Config(), autostart=True)
    test_bucket: List[Event] = []

    def append_to_bucket(
        bucket: List[Event],
    ) -> Callable[[Event], Awaitable[None]]:
        async def _append_to_bucket(event: Event):
            bucket.append(event)

        return _append_to_bucket

    lid1 = event_bus.add_listener(append_to_bucket(test_bucket))
    lid2 = event_bus.add_listener(
        append_to_bucket(test_bucket), [EventType.STUDY_CREATED]
    )
    event_bus.push(
        Event(
            type=EventType.STUDY_JOB_STARTED,
            payload="foo",
            permissions=PermissionInfo(public_mode=PublicMode.READ),
        )
    )
    event_bus.push(
        Event(
            type=EventType.STUDY_CREATED,
            payload="foo",
            permissions=PermissionInfo(public_mode=PublicMode.READ),
        )
    )
    autoretry_assert(lambda: len(test_bucket) == 3, 2)

    event_bus.remove_listener(lid1)
    event_bus.remove_listener(lid2)
    test_bucket.clear()
    event_bus.push(
        Event(
            type=EventType.STUDY_JOB_STARTED,
            payload="foo",
            permissions=PermissionInfo(public_mode=PublicMode.READ),
        )
    )
    autoretry_assert(lambda: len(test_bucket) == 0, 2)

    queue_name = "some work job"
    event_bus.add_queue_consumer(append_to_bucket(test_bucket), queue_name)
    event_bus.add_queue_consumer(
        lambda event: test_bucket.append(event), queue_name
    )
    event_bus.queue(
        Event(
            type=EventType.WORKER_TASK,
            payload="worker task",
            permissions=PermissionInfo(public_mode=PublicMode.READ),
        ),
        queue_name,
    )
    autoretry_assert(lambda: len(test_bucket) == 1, 2)
