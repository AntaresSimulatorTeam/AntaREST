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
from typing import List

from typing_extensions import override

from antarest.study.business.model.layer_model import LayerCreation, Layer
from antarest.study.storage.rawstudy.model.filesystem.config.layer import LayerFileData
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.model.command.common import CommandName, CommandOutput
from antarest.study.storage.variantstudy.model.command.icommand import ICommand
from antarest.study.storage.variantstudy.model.command_listener.command_listener import ICommandListener
from antarest.study.storage.variantstudy.model.model import CommandDTO


class CreateLayer(ICommand):
    """
    Command used to create a layer.
    """

    # Overloaded metadata
    # ===================

    command_name: CommandName = CommandName.CREATE_LAYER

    # Command parameters
    # ==================
    parameters: LayerCreation

    @override
    def _apply(self, study_data: FileStudy, listener: ICommandListener | None = None) -> CommandOutput:
        layers = study_data.tree.get(["layers", "layers", "layers"])

        current_layers = LayerFileData.model_validate({"layers": layers})

        new_id = max((int(layer) for layer in layers), default=0) + 1

        current_layers.layers[str(new_id)] = self.parameters.name

        study_data.tree.save(current_layers.model_dump(exclude_none=True), ["layers", "layers", "layers"])

        return CommandOutput(status=True, message=f"Layer {self.parameters.name} created successfully")


    def to_dto(self) -> CommandDTO:
        pass

    def get_inner_matrices(self) -> List[str]:
        return []