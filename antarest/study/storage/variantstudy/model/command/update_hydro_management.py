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

from typing import Any, List, Optional

from typing_extensions import override

from antarest.study.business.model.hydro_management_model import HYDRO_PATH, HydroManagementOptions
from antarest.study.storage.rawstudy.model.filesystem.config.model import FileStudyTreeConfig
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.model.command.common import CommandName, CommandOutput
from antarest.study.storage.variantstudy.model.command.icommand import ICommand, OutputTuple
from antarest.study.storage.variantstudy.model.command_listener.command_listener import ICommandListener
from antarest.study.storage.variantstudy.model.model import CommandDTO


def normalize_key(key: str) -> str:
    return key.replace(" ", "").replace("-", "").replace("_", "").lower()


def update_current_for_area(area: str, current: dict[str, Any], new: dict[str, Any]) -> dict[str, Any]:
    normalized_current = {normalize_key(key): key for key in current}

    for new_key, new_value in new.items():
        norm_new_key = normalize_key(new_key)
        if norm_new_key in normalized_current:
            current_key = normalized_current[norm_new_key]
            if area in current[current_key]:
                current[current_key][area] = new_value
            else:
                current[current_key][area] = new_value
        else:
            current[new_key] = {area: new_value}

    return current


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

        updated_current = update_current_for_area(self.area_id, current_hydro, new_hydro)

        study_data.tree.save(updated_current, HYDRO_PATH)

        output, _ = self._apply_config(study_data.config)

        return output

    @override
    def to_dto(self) -> CommandDTO:
        return CommandDTO(
            action=CommandName.UPDATE_HYDRO_MANAGEMENT.value,
            args={"area_id": self.area_id, "properties": self.properties},
            study_version=self.study_version,
        )

    @override
    def get_inner_matrices(self) -> List[str]:
        return []
