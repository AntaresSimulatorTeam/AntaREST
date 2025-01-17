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

from enum import StrEnum


class MaintenanceMode(StrEnum):
    NORMAL_MODE = "NORMAL"
    MAINTENANCE_MODE = "MAINTENANCE"

    @classmethod
    def from_bool(cls, flag: bool) -> "MaintenanceMode":
        return {False: cls.NORMAL_MODE, True: cls.MAINTENANCE_MODE}[flag]

    def __bool__(self) -> bool:
        cls = self.__class__
        return {cls.NORMAL_MODE: False, cls.MAINTENANCE_MODE: True}[self]
