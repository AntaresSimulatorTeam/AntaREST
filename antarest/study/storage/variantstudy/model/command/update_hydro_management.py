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

from antarest.study.business.model.hydro_model import (
    HYDRO_PATH,
    HydroProperties,
    HydroPropertiesInternal,
    get_hydro_id,
)
from antarest.study.storage.rawstudy.model.filesystem.config.model import FileStudyTreeConfig
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.model.command.common import CommandName, CommandOutput
from antarest.study.storage.variantstudy.model.command.icommand import ICommand, OutputTuple
from antarest.study.storage.variantstudy.model.command_listener.command_listener import ICommandListener
from antarest.study.storage.variantstudy.model.model import CommandDTO


class UpdateHydroProperties(ICommand):
    """
    Command used to update hydro properties in an area.
    """

    # Overloaded metadata
    # ===================

    command_name: CommandName = CommandName.UPDATE_HYDRO_PROPERTIES

    # Command parameters
    # ==================

    area_id: str
    properties: HydroProperties

    @override
    def _apply_config(self, study_data: FileStudyTreeConfig) -> OutputTuple:
        return CommandOutput(status=True, message=f"Hydro properties in '{self.area_id}' updated."), {}

    @override
    def _apply(self, study_data: FileStudy, listener: Optional[ICommandListener] = None) -> CommandOutput:
        current_hydro = study_data.tree.get(HYDRO_PATH)
        new_hydro = self.properties.model_dump(exclude_unset=True)

        area_id = get_hydro_id(area_id=self.area_id, field_dict=current_hydro)

        new = HydroPropertiesInternal.model_validate(new_hydro).model_dump(by_alias=True, exclude_unset=True)

        for k, v in new.items():
            current_hydro.setdefault(k, {}).update({area_id: v})

        study_data.tree.save(current_hydro, HYDRO_PATH)

        output, _ = self._apply_config(study_data.config)

        return output

    @override
    def to_dto(self) -> CommandDTO:
        return CommandDTO(
            action=CommandName.UPDATE_HYDRO_PROPERTIES.value,
            args={"area_id": self.area_id, "properties": self.properties.model_dump(mode="json")},
            study_version=self.study_version,
        )

    @override
    def get_inner_matrices(self) -> List[str]:
        return []
