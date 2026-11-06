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

from abc import ABC, abstractmethod

from antarest.study.business.model.gems.calendar import GemsCalendar


class ReadOnlyGemsCalendarDao(ABC):
    @abstractmethod
    def get_gems_calendar(self) -> GemsCalendar | None:
        """Return the GEMS calendar, or None if not configured."""
        raise NotImplementedError()


class GemsCalendarDao(ReadOnlyGemsCalendarDao):
    @abstractmethod
    def save_gems_calendar(self, calendar: GemsCalendar) -> None:
        """Save or replace the GEMS calendar for the study."""
        raise NotImplementedError()
