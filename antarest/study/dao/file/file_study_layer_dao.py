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
from antarest.study.business.model.layer_model import Layer
from antarest.study.dao.api.layer_dao import LayerDao
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
    def save_layer(self, layer: Layer) -> None:
        file_study = self.get_file_study()

        file_study.tree.save(layer.name, ["layers", "layers", "layers", layer.id])

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
