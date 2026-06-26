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

from antarest.core.utils.fastapi_sqlalchemy import db
from antarest.launcher.model import LauncherLoad

if TYPE_CHECKING:
    from antarest.launcher.service import LauncherService


class DataBaseLauncherLoadDao:
    def update_launcher_load(self, launcher_load: LauncherLoad) -> None:
        db.session.merge(launcher_load)
        db.session.commit()

    def get_launchers_loads(self) -> list[LauncherLoad]:
        return db.session.query(LauncherLoad).all()

    def get_launcher_load(self, launcher_name: str) -> LauncherLoad | None:
        return db.session.get(LauncherLoad, launcher_name)

    def update_all_launcher_loads(self, service: "LauncherService") -> None:
        for launcher_id, dto in service.get_all_loads().items():
            self.update_launcher_load(LauncherLoad.from_dto(dto, launcher_id))
