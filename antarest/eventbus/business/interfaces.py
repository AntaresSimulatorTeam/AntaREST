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

import abc
from abc import abstractmethod
from typing import List, Optional

from antarest.core.interfaces.eventbus import Event


class IEventBusBackend(abc.ABC):
    @abstractmethod
    def push_event(self, event: Event) -> None:
        raise NotImplementedError

    @abstractmethod
    def queue_event(self, event: Event, queue: str) -> None:
        raise NotImplementedError

    @abstractmethod
    def pull_queue(self, queue: str) -> Optional[Event]:
        raise NotImplementedError

    @abstractmethod
    def get_events(self) -> List[Event]:
        raise NotImplementedError

    @abstractmethod
    def clear_events(self) -> None:
        raise NotImplementedError
