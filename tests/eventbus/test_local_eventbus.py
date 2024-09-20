# Copyright (c) 2024, RTE (https://www.rte-france.com)
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

from antarest.core.interfaces.eventbus import Event, EventType
from antarest.core.model import PermissionInfo, PublicMode
from antarest.eventbus.business.local_eventbus import LocalEventBus


def test_lifecycle():
    eventbus = LocalEventBus()
    event = Event(
        type=EventType.STUDY_EDITED,
        payload="foo",
        permissions=PermissionInfo(public_mode=PublicMode.READ),
    )
    eventbus.push_event(event)
    assert eventbus.get_events() == [event]
    eventbus.clear_events()
    assert len(eventbus.get_events()) == 0
