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
from abc import ABC, abstractmethod
from typing import Sequence

from typing_extensions import override

from antarest.core.exceptions import LayerNotAllowedToBeDeleted, LayerNotFound
from antarest.study.business.areas.area_utils import _get_area_layers, _get_ui_info_map
from antarest.study.business.model.layer_model import Layer, LayerUpdate
from antarest.study.dao.api.layer_dao import LayerDao
from antarest.study.storage.rawstudy.model.filesystem.config.layer import serialize_layers
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy


class FileStudyLayerDao(LayerDao, ABC):
    @abstractmethod
    def get_file_study(self) -> FileStudy:
        pass

    @override
    def get_layers(self) -> Sequence[Layer]:
        file_study = self.get_file_study()
        area_ids = list(file_study.config.areas)
        ui_info_map = _get_ui_info_map(file_study, area_ids)
        layers = file_study.tree.get(["layers", "layers", "layers"])
        if not layers:
            layers["0"] = "All"
        return [
            Layer(
                id=str(layer),
                name=layers[str(layer)],
                areas=[
                    area
                    for area in ui_info_map
                    if str(layer) in _get_area_layers(ui_info_map, area)
                    # the layer 0 always display all areas
                    or str(layer) == "0"
                ],
            )
            for layer in layers
        ]

    @override
    def save_layers(self, layer: Layer) -> None:
        current_layers = list(self.get_layers())

        new_id = max((int(layer.id) for layer in current_layers if layer.id is not None), default=0) + 1
        layer.id = str(new_id)

        current_layers.append(layer)

        serialized_layers = serialize_layers(current_layers)

        file_study = self.get_file_study()
        file_study.tree.save(serialized_layers.layers, ["layers", "layers", "layers"])

    @override
    def delete_layer(self, layer: Layer) -> None:
        layer_id = layer.id

        if layer_id == "0":
            raise LayerNotAllowedToBeDeleted("You can not delete the layer 0, it is used to display all areas")

        file_study = self.get_file_study()

        layers = file_study.tree.get(["layers", "layers", "layers"])

        if layer_id not in layers:
            raise LayerNotFound

        del layers[layer_id]

        file_study.tree.save(layers, ["layers", "layers", "layers"])

    @override
    def update_layer_name(self, layer: LayerUpdate) -> None:
        new_layer = layer
        file_study = self.get_file_study()
        layers = file_study.tree.get(["layers", "layers", "layers"])

        if layer.id not in [str(layer) for layer in list(layers.keys())]:
            raise LayerNotFound

        layers[new_layer.id] = new_layer.name

        file_study.tree.save(layers, ["layers", "layers", "layers"])
