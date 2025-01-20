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
from typing import Dict, List, Optional

from typing_extensions import override

from antarest.core.interfaces.eventbus import Event
from antarest.eventbus.business.interfaces import IEventBusBackend

logger = logging.getLogger(__name__)


class LocalEventBus(IEventBusBackend):
    def __init__(self) -> None:
        self.events: List[Event] = []
        self.queues: Dict[str, List[Event]] = {}

    @override
    def push_event(self, event: Event) -> None:
        self.events.append(event)

    @override
    def get_events(self) -> List[Event]:
        return self.events

    @override
    def clear_events(self) -> None:
        self.events.clear()

    @override
    def queue_event(self, event: Event, queue: str) -> None:
        if queue not in self.queues:
            self.queues[queue] = []
        self.queues[queue].append(event)

    @override
    def pull_queue(self, queue: str) -> Optional[Event]:
        if queue in self.queues and len(self.queues[queue]) > 0:
            return self.queues[queue].pop(0)
        return None
