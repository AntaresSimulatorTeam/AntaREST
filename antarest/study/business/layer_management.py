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
from typing import List

from antarest.core.exceptions import LayerNotAllowedToBeDeleted, LayerNotFound
from antarest.study.business.model.layer_model import Layer, LayerCreation, LayerUpdate
from antarest.study.business.study_interface import StudyInterface
from antarest.study.storage.variantstudy.model.command.create_layer import CreateLayer
from antarest.study.storage.variantstudy.model.command.remove_layer import RemoveLayer
from antarest.study.storage.variantstudy.model.command.update_layer import UpdateLayer
from antarest.study.storage.variantstudy.model.command_context import CommandContext


class LayerManager:
    def __init__(self, command_context: CommandContext) -> None:
        self._command_context = command_context

    def get_layers(self, study: StudyInterface) -> List[Layer]:
        return list(study.get_study_dao().get_layers())

    def create_layer(self, study: StudyInterface, layer_name: str) -> str:
        current_layers = list(study.get_study_dao().get_layers())
        layer_id = str(max((int(layer.id) for layer in current_layers if layer.id is not None), default=0) + 1)

        command = CreateLayer(
            parameters=LayerCreation(id=layer_id, name=layer_name),
            command_context=self._command_context,
            study_version=study.version,
        )
        study.add_commands([command])

        return layer_id

    def update_layer_name(self, study: StudyInterface, layer_id: str, layer_name: str) -> None:
        command = UpdateLayer(
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

        if layer_id == "0":
            raise LayerNotAllowedToBeDeleted(layer_id)

        if not self.layer_exists(study, layer_id):
            raise LayerNotFound

        command = RemoveLayer(
            layer_id=layer_id,
            command_context=self._command_context,
            study_version=study.version,
        )

        study.add_commands([command])

    def layer_exists(self, study: StudyInterface, layer_id: str) -> bool:
        return study.get_study_dao().layer_exists(layer_id)
