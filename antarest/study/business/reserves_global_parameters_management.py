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
from antarest.study.business.model.reserves_global_parameters_model import (
    ReservesGlobalParameters,
    ReservesGlobalParametersUpdate,
)
from antarest.study.business.study_interface import StudyInterface
from antarest.study.storage.variantstudy.model.command.update_reserves_global_parameters import (
    UpdateReservesGlobalParameters,
)
from antarest.study.storage.variantstudy.model.command_context import CommandContext


class ReservesGlobalParametersManager:
    def __init__(self, command_context: CommandContext) -> None:
        self._command_context = command_context

    def get_reserves_global_parameters(self, study: StudyInterface, area_id: str) -> ReservesGlobalParameters:
        return study.get_study_dao().get_reserves_global_parameters(area_id)

    def update_reserves_global_parameters(
        self,
        study: StudyInterface,
        area_id: str,
        parameters: ReservesGlobalParametersUpdate,
    ) -> ReservesGlobalParameters:
        command = UpdateReservesGlobalParameters(
            properties={area_id: parameters},
            command_context=self._command_context,
            study_version=study.version,
        )
        study.add_commands([command])
        return study.get_study_dao().get_reserves_global_parameters(area_id)
