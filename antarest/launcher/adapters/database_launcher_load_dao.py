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


from sqlalchemy.orm import DeclarativeBase, Session

from antarest.launcher.model import LauncherLoad


class Base(DeclarativeBase):
    pass


class DataBaseLauncherLoadDao(DeclarativeBase):
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
