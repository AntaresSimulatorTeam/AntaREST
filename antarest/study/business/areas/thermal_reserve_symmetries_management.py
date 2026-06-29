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
from antarest.study.business.model.reserve_symmetries_model import ReserveSymmetry
from antarest.study.business.study_interface import StudyInterface
from antarest.study.dao.common import ThermalId
from antarest.study.storage.variantstudy.model.command.replace_thermal_reserve_symmetries import (
    ReplaceThermalReserveSymmetries,
)
from antarest.study.storage.variantstudy.model.command_context import CommandContext


class ThermalReserveSymmetriesManager:
    def __init__(self, command_context: CommandContext) -> None:
        self._command_context = command_context

    def get_symmetries(self, study: StudyInterface, area_id: str) -> dict[ThermalId, list[ReserveSymmetry]]:
        return study.get_study_dao().get_thermal_reserve_symmetries(area_id)

    def set_symmetries(
        self, study: StudyInterface, area_id: str, thermal_id: str, symmetries: list[ReserveSymmetry]
    ) -> list[ReserveSymmetry]:
        command = ReplaceThermalReserveSymmetries(
            area_id=area_id,
            thermal_id=thermal_id,
            symmetries=symmetries,
            command_context=self._command_context,
            study_version=study.version,
        )
        study.add_commands([command])
        return self.get_symmetries(study, area_id)[thermal_id]
