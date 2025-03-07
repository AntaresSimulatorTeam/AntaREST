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

from typing import List, Optional

from typing_extensions import override

from antarest.study.business.model.hydro_management_model import (
    HYDRO_PATH,
    HydroManagementOptions,
    get_hydro_id,
)
from antarest.study.storage.rawstudy.model.filesystem.config.model import FileStudyTreeConfig
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.model.command.common import CommandName, CommandOutput
from antarest.study.storage.variantstudy.model.command.icommand import ICommand, OutputTuple
from antarest.study.storage.variantstudy.model.command_listener.command_listener import ICommandListener
from antarest.study.storage.variantstudy.model.model import CommandDTO

mapping = {
    "inter_daily_breakdown": "inter-daily-breakdown",
    "intra_daily_modulation": "intra-daily-modulation",
    "inter_monthly_breakdown": "inter-monthly-breakdown",
    "reservoir": "reservoir",
    "reservoir_capacity": "reservoir capacity",
    "follow_load": "follow load",
    "use_water": "use water",
    "hard_bounds": "hard bounds",
    "initialize_reservoir_date": "initialize reservoir date",
    "use_heuristic": "use heuristic",
    "power_to_level": "power to level",
    "use_leeway": "use leeway",
    "leeway_low": "leeway low",
    "leeway_up": "leeway up",
    "pumping_efficiency": "pumping efficiency",
}


class UpdateHydroManagement(ICommand):
    """
    Command used to update a hydro management options in an area.
    """

    # Overloaded metadata
    # ===================

    command_name: CommandName = CommandName.UPDATE_HYDRO_MANAGEMENT

    # Command parameters
    # ==================

    area_id: str
    properties: HydroManagementOptions

    @override
    def _apply_config(self, study_data: FileStudyTreeConfig) -> OutputTuple:
        return CommandOutput(status=True, message=f"Hydro management '{self.area_id}' updated."), {}

    @override
    def _apply(self, study_data: FileStudy, listener: Optional[ICommandListener] = None) -> CommandOutput:
        current_hydro = study_data.tree.get(HYDRO_PATH)
        new_hydro = self.properties.model_dump(exclude_unset=True)

        area_id = get_hydro_id(area_id=self.area_id, field_dict=current_hydro)

        for k, v in new_hydro.items():
            if key := mapping.get(k, None):
                current_hydro.setdefault(key, {}).update({area_id: v})

        study_data.tree.save(current_hydro, HYDRO_PATH)

        output, _ = self._apply_config(study_data.config)

        return output

    @override
    def to_dto(self) -> CommandDTO:
        return CommandDTO(
            action=CommandName.UPDATE_HYDRO_MANAGEMENT.value,
            args={"area_id": self.area_id, "properties": self.properties.model_dump(mode="json")},
            study_version=self.study_version,
        )

    @override
    def get_inner_matrices(self) -> List[str]:
        return []
