import json
import logging
from typing import List, Optional

import dataclasses
import redis
from redis.client import Redis

from antarest.core.config import RedisConfig
from antarest.core.interfaces.eventbus import Event
from antarest.eventbus.business.interfaces import IEventBusBackend

logger = logging.getLogger(__name__)
REDIS_STORE_KEY = "events"


class RedisEventBus(IEventBusBackend):
    def __init__(
        self, redis_conf: RedisConfig, redis_client: Optional[Redis] = None
    ) -> None:
        self.redis = (
            redis_client
            if redis_client is not None
            else redis.Redis(host=redis_conf.host, port=redis_conf.port, db=0)
        )
        self.pubsub = self.redis.pubsub()
        self.pubsub.subscribe(REDIS_STORE_KEY)

    def push_event(self, event: Event) -> None:
        self.redis.publish(
            REDIS_STORE_KEY, json.dumps(dataclasses.asdict(event))
        )

    def get_events(self) -> List[Event]:
        try:
            event = self.pubsub.get_message(ignore_subscribe_messages=True)
            if event is not None:
                return [Event(**json.loads(event["data"]))]
        except Exception as e:
            logger.error("Failed to retrieve or parse event !", exc_info=e)

        return []

    def clear_events(self) -> None:
        # Nothing to do
        pass
