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

from antarest.study.business.model.layer_model import Layer
from antarest.study.dao.api.study_dao import StudyDao
from antarest.study.storage.variantstudy.model.command.common import CommandName, CommandOutput, command_succeeded
from antarest.study.storage.variantstudy.model.command.icommand import ICommand
from antarest.study.storage.variantstudy.model.command_listener.command_listener import ICommandListener
from antarest.study.storage.variantstudy.model.model import CommandDTO


class RemoveLayer(ICommand):
    """
    Command used to remove a layer
    """

    # Overloaded metadata
    # ===================

    command_name: CommandName = CommandName.REMOVE_LAYER

    # Command parameters
    # ==================

    layer_id: str

    @override
    def _apply_dao(self, study_data: StudyDao, listener: ICommandListener | None = None) -> CommandOutput:
        study_data.delete_layer(Layer(id=self.layer_id))
        return command_succeeded(f"Layer {self.layer_id} deleted successfully.")

    @override
    def to_dto(self) -> CommandDTO:
        return CommandDTO(
            action=CommandName.REMOVE_LAYER.value,
            args={"layer_id": self.layer_id},
            study_version=self.study_version,
        )
