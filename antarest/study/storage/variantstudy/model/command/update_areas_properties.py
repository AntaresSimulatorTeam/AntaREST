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
from typing import Dict, Optional

from typing_extensions import override

from antarest.study.business.model.area_properties_model import AreaPropertiesUpdate, update_area_properties
from antarest.study.dao.api.study_dao import StudyDao
from antarest.study.storage.variantstudy.model.command.common import CommandName, CommandOutput, command_succeeded
from antarest.study.storage.variantstudy.model.command.icommand import ICommand
from antarest.study.storage.variantstudy.model.command_listener.command_listener import ICommandListener
from antarest.study.storage.variantstudy.model.model import CommandDTO


class UpdateAreasProperties(ICommand):
    """
    Command used to update multiple areas properties
    """

    # Overloaded metadata
    # ===================

    command_name: CommandName = CommandName.UPDATE_AREAS_PROPERTIES

    # Command parameters
    # ==================
    properties: Dict[str, AreaPropertiesUpdate]

    @override
    def _apply_dao(self, study_data: StudyDao, listener: Optional[ICommandListener] = None) -> CommandOutput:
        for area_id, area_properties in self.properties.items():
            current_properties = study_data.get_area_properties(area_id)

            new_properties = update_area_properties(current_properties, area_properties)

            study_data.save_area_properties(area_id, new_properties)

        updated_areas = ", ".join(self.properties.keys())
        return command_succeeded(message=f"Areas properties updated: {updated_areas}")

    @override
    def to_dto(self) -> CommandDTO:
        return CommandDTO(
            action=CommandName.UPDATE_AREAS_PROPERTIES.value,
            args={
                "properties": {
                    area_id: props.model_dump(mode="json", exclude_none=True)
                    for area_id, props in self.properties.items()
                },
            },
            study_version=self.study_version,
        )
