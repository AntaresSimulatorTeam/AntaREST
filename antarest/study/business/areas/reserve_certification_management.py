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
from antarest.study.business.model.thermal_reserve_certification_model import (
    ReserveCertifications,
)
from antarest.study.business.study_interface import StudyInterface
from antarest.study.storage.variantstudy.model.command.icommand import ICommand
from antarest.study.storage.variantstudy.model.command.replace_thermal_reserve_certifications import (
    ReplaceThermalReserveCertifications,
)
from antarest.study.storage.variantstudy.model.command_context import CommandContext


class ReserveCertificationsManager:
    def __init__(self, command_context: CommandContext) -> None:
        self._command_context = command_context

    def get_certifications(self, study: StudyInterface, area_id: str) -> ReserveCertifications:
        thermals = study.get_study_dao().get_all_thermal_reserve_certifications_for_area(area_id)
        return ReserveCertifications(thermals=thermals)

    def set_certifications(
        self,
        study: StudyInterface,
        area_id: str,
        data: ReserveCertifications,
    ) -> ReserveCertifications:
        commands: list[ICommand] = []

        # Thermals part
        if data.thermals:
            command = ReplaceThermalReserveCertifications(
                area_id=area_id,
                certifications=data.thermals,
                study_version=study.version,
                command_context=self._command_context,
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
