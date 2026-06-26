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

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy.orm import Session

from antarest.launcher.model import LauncherLoad

if TYPE_CHECKING:
    from antarest.launcher.service import LauncherService


class DataBaseLauncherLoadDao:
    def __init__(
        self,
        session: Session,
    ) -> None:
        super().__init__()
        self._session = session
        self.launchers_loads: dict[str, LauncherLoad] = {}

    def update_launcher_load(self, launcher_load: LauncherLoad) -> None:
        self.launchers_loads[launcher_load.launcher_name] = launcher_load
        self.__save_launcher_load(launcher_load)

    def __save_launcher_load(self, launcher_load: LauncherLoad) -> None:
        self._session.merge(launcher_load)
        self._session.commit()

    def get_launchers_loads(self) -> list[LauncherLoad]:
        return self._session.query(LauncherLoad).all()

    def update_all_launcher_loads(self, service: "LauncherService") -> None:
        launcher_loads_dtos_by_id = service.get_all_loads()
        for id, dto in launcher_loads_dtos_by_id.items():
            launcher_load: LauncherLoad = LauncherLoad.from_dto(dto, id)
            self.update_launcher_load(launcher_load)
