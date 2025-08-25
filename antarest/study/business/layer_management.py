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

from antarest.study.business.model.layer_model import Layer, LayerCreation, LayerUpdate
from antarest.study.business.study_interface import StudyInterface
from antarest.study.storage.variantstudy.model.command.create_layer import CreateLayer
from antarest.study.storage.variantstudy.model.command.remove_layer import RemoveLayer
from antarest.study.storage.variantstudy.model.command.update_layer_name import UpdateLayerName
from antarest.study.storage.variantstudy.model.command_context import CommandContext


class LayerManager:
    def __init__(self, command_context: CommandContext) -> None:
        self._command_context = command_context

    def get_layers(self, study: StudyInterface) -> List[Layer]:
        return list(study.get_study_dao().get_layers())

    def create_layer(self, study: StudyInterface, layer_name: str) -> str:
        command = CreateLayer(
            parameters=LayerCreation(name=layer_name),
            command_context=self._command_context,
            study_version=study.version,
        )
        study.add_commands([command])
        return layer_name

    def update_layer_name(self, study: StudyInterface, layer_id: str, layer_name: str) -> None:
        command = UpdateLayerName(
            parameters=LayerUpdate(id=layer_id, name=layer_name),
            command_context=self._command_context,
            study_version=study.version,
        )
        study.add_commands([command])

    def remove_layer(self, study: StudyInterface, layer_id: str) -> None:
        """
        Remove a layer from a study.

        Raises:
            LayerNotAllowedToBeDeleted: If the layer ID is "0".
            LayerNotFound: If the layer ID is not found.
        """
        command = RemoveLayer(
            parameters=Layer(id=layer_id),
            command_context=self._command_context,
            study_version=study.version,
        )

        study.add_commands([command])
