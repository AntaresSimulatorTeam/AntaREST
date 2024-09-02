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

from unittest.mock import Mock

from antarest.core.interfaces.eventbus import Event, EventType
from antarest.core.model import PermissionInfo, PublicMode
from antarest.eventbus.business.redis_eventbus import RedisEventBus


def test_lifecycle():
    redis_client = Mock()
    pubsub_mock = Mock()
    redis_client.pubsub.return_value = pubsub_mock
    eventbus = RedisEventBus(redis_client)
    pubsub_mock.subscribe.assert_called_once_with("events")

    event = Event(
        type=EventType.STUDY_EDITED,
        payload="foo",
        permissions=PermissionInfo(public_mode=PublicMode.READ),
    )
    serialized = event.json()
    pubsub_mock.get_message.return_value = {"data": serialized}
    eventbus.push_event(event)
    redis_client.publish.assert_called_once_with("events", serialized)
    assert eventbus.get_events() == [event]
