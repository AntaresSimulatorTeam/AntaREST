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


from typing_extensions import override

from antarest.study.dao.api.study_dao import StudyDao
from antarest.study.storage.variantstudy.model.command.common import CommandName, CommandOutput, command_succeeded
from antarest.study.storage.variantstudy.model.command.icommand import ICommand
from antarest.study.storage.variantstudy.model.command_listener.command_listener import ICommandListener
from antarest.study.storage.variantstudy.model.model import CommandDTO


class ReplaceLayerAreas(ICommand):
    """
    Command used to replace the areas associated with a specific layer.
    This command completely replaces the list of areas in the layer.
    """

    # Overloaded metadata
    # ===================

    command_name: CommandName = CommandName.REPLACE_LAYER_AREAS

    # Command parameters
    # ==================

    layer_id: str
    area_ids: list[str]

    @override
    def _apply_dao(self, study_data: StudyDao, listener: ICommandListener | None = None) -> CommandOutput[None]:
        study_data.save_layer_areas(self.layer_id, self.area_ids)
        return command_succeeded(message=f"Layer '{self.layer_id}' areas replaced", result=None)

    @override
    def to_dto(self) -> CommandDTO:
        return CommandDTO(
            action=CommandName.REPLACE_LAYER_AREAS.value,
            args={"layer_id": self.layer_id, "area_ids": self.area_ids},
            study_version=self.study_version,
        )
