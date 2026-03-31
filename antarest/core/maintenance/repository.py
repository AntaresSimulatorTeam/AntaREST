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


from antarest.core.configdata.model import ConfigData, ConfigDataAppKeys
from antarest.core.configdata.repository import ConfigDataRepository
from antarest.core.jwt import DEFAULT_ADMIN_USER


class MaintenanceRepository(ConfigDataRepository):
    def save_maintenance_mode(self, mode: str) -> None:
        self.save(
            ConfigData(
                owner=DEFAULT_ADMIN_USER.id,
                key=ConfigDataAppKeys.MAINTENANCE_MODE.value,
                value=mode,
            )
        )

    def save_message_info(self, message: str) -> None:
        self.save(
            ConfigData(
                owner=DEFAULT_ADMIN_USER.id,
                key=ConfigDataAppKeys.MESSAGE_INFO.value,
                value=message,
            )
        )

    def get_maintenance_mode(self) -> str | None:
        config_data = self.get(
            owner=DEFAULT_ADMIN_USER.id,
            key=ConfigDataAppKeys.MAINTENANCE_MODE.value,
        )
        if config_data is not None:
            return str(config_data.value)
        return None

    def get_message_info(self) -> str | None:
        config_data = self.get(
            owner=DEFAULT_ADMIN_USER.id,
            key=ConfigDataAppKeys.MESSAGE_INFO.value,
        )
        if config_data is not None:
            return str(config_data.value)
        return None
