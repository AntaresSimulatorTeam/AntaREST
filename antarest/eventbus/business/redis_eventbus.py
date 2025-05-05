# Copyright (c) 2025, RTE (https://www.rte-france.com)
#
# See AUTHORS.txt
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# SPDX-License-Identifier: MPL-2.0
#
# This file is part of the Antares project.

import logging
import pathlib
from typing import List, Optional, cast

from redis.client import Redis
from typing_extensions import override

from antarest.core.interfaces.eventbus import Event
from antarest.eventbus.business.interfaces import IEventBusBackend

logger = logging.getLogger(__name__)
REDIS_STORE_KEY = "events"
MAX_EVENTS_LIST_SIZE = 1000


class RedisEventBus(IEventBusBackend):
    def __init__(self, redis_client: Redis) -> None:  # type: ignore
        self.redis = redis_client
        self.pubsub = self.redis.pubsub()
        self.pubsub.subscribe(REDIS_STORE_KEY)

    @override
    def push_event(self, event: Event) -> None:
        self.redis.publish(REDIS_STORE_KEY, event.model_dump_json())

    @override
    def queue_event(self, event: Event, queue: str) -> None:
        self.redis.rpush(queue, event.model_dump_json())

    @override
    def pull_queue(self, queue: str) -> Optional[Event]:
        event = self.redis.lpop(queue)
        if event:
            event_string = pathlib.Path(event).read_text()
            return cast(Optional[Event], Event.model_validate_json(event_string))
        return None

    @override
    def get_events(self) -> List[Event]:
        messages = []
        try:
            while msg := self.pubsub.get_message(ignore_subscribe_messages=True):
                messages.append(msg)
                if len(messages) >= MAX_EVENTS_LIST_SIZE:
                    break
        except Exception:
            logger.error("Failed to retrieve events !", exc_info=True)

        events = []
        for msg in messages:
            try:
                events.append(Event.model_validate_json(msg["data"]))
            except Exception:
                logger.error(f"Failed to parse event ! {msg}", exc_info=True)

        return events

    @override
    def clear_events(self) -> None:
        # Nothing to do
        pass
