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
from antarest.study.business.model.reserve_symmetries_model import ReserveSymmetries
from antarest.study.business.study_interface import StudyInterface
from antarest.study.storage.variantstudy.model.command.icommand import ICommand
from antarest.study.storage.variantstudy.model.command.replace_thermal_reserve_symmetries import (
    ReplaceThermalReserveSymmetries,
)
from antarest.study.storage.variantstudy.model.command_context import CommandContext


class ReserveSymmetriesManager:
    def __init__(self, command_context: CommandContext) -> None:
        self._command_context = command_context

    def get_symmetries(self, study: StudyInterface, area_id: str) -> ReserveSymmetries:
        thermals = study.get_study_dao().get_thermal_reserve_symmetries(area_id)
        return ReserveSymmetries(thermals=thermals)

    def set_symmetries(self, study: StudyInterface, area_id: str, data: ReserveSymmetries) -> ReserveSymmetries:
        commands: list[ICommand] = []

        # Thermal part
        if data.thermals:
            command = ReplaceThermalReserveSymmetries(
                area_id=area_id,
                symmetries=data.thermals,
                command_context=self._command_context,
                study_version=study.version,
            )
            commands.append(command)

        # St-Storage part
        # todo

        # Hydro part
        # todo

        # Apply the modifications
        if commands:
            study.add_commands(commands)
        return data
