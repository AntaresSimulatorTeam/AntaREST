# Copyright (c) 2026, RTE (https://www.rte-france.com)
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


from antarest.core.interfaces.eventbus import Event, EventType, IEventBus
from antarest.core.model import PermissionInfo
from antarest.study.model import (
    Study,
)


def notify_study_data_edition(event_bus: IEventBus, study: Study) -> None:
    event_bus.push(
        Event(
            type=EventType.STUDY_DATA_EDITED,
            payload=study.to_json_summary(),
            permissions=PermissionInfo.from_study(study),
        )
    )


def notify_study_edition(event_bus: IEventBus, study: Study) -> None:
    event_bus.push(
        Event(
            type=EventType.STUDY_EDITED,
            payload=study.to_json_summary(),
            permissions=PermissionInfo.from_study(study),
        )
    )


def notify_study_creation(event_bus: IEventBus, study: Study) -> None:
    event_bus.push(
        Event(
            type=EventType.STUDY_CREATED,
            payload=study.to_json_summary(),
            permissions=PermissionInfo.from_study(study),
        )
    )
