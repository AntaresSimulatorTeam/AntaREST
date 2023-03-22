import dataclasses
import json
import logging
from typing import List, Optional, cast

from redis.client import Redis

from antarest.core.interfaces.eventbus import Event
from antarest.eventbus.business.interfaces import IEventBusBackend

logger = logging.getLogger(__name__)
REDIS_STORE_KEY = "events"


class RedisEventBus(IEventBusBackend):
    def __init__(self, redis_client: Redis) -> None:  # type: ignore
        self.redis = redis_client
        self.pubsub = self.redis.pubsub()
        self.pubsub.subscribe(REDIS_STORE_KEY)

    def push_event(self, event: Event) -> None:
        self.redis.publish(REDIS_STORE_KEY, event.json())

    def queue_event(self, event: Event, queue: str) -> None:
        self.redis.rpush(queue, event.json())

    def pull_queue(self, queue: str) -> Optional[Event]:
        event = self.redis.lpop(queue)
        if event:
            return cast(Optional[Event], Event.parse_raw(event))
        return None

    def get_events(self) -> List[Event]:
        try:
            event = self.pubsub.get_message(ignore_subscribe_messages=True)
            if event is not None:
                return [Event.parse_raw(event["data"])]
        except Exception:
            logger.error("Failed to retrieve or parse event !", exc_info=True)

        return []

    def clear_events(self) -> None:
        # Nothing to do
        pass
