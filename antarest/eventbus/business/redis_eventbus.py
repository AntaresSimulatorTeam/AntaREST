import json
import logging
import dataclasses
import redis

from typing import Any, List, Optional
from dataclasses import dataclass
from redis.client import Redis

from antarest.common.interfaces.eventbus import Event
from antarest.eventbus.business.interfaces import IEventBusBackend
from antarest.eventbus.config import RedisConfig

logger = logging.getLogger(__name__)
REDIS_STORE_KEY = "events"


class RedisEventBus(IEventBusBackend):
    def __init__(
        self,
        redis_conf_dict: RedisConfig,
        redis_client: Optional[Redis] = None,
    ) -> None:
        redis_conf = redis_conf_dict
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
