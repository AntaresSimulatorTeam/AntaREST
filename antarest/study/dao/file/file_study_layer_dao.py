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
import re
from abc import ABC, abstractmethod
from collections.abc import Sequence
from typing import Any

from typing_extensions import override

from antarest.study.business.model.area_model import DEFAULT_LAYER_ID, DEFAULT_LAYER_NAME
from antarest.study.business.model.layer_model import Layer
from antarest.study.dao.api.layer_dao import LayerDao
from antarest.study.storage.rawstudy.model.filesystem.config.area import AreaUIFileData
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy


class FileStudyLayerDao(LayerDao, ABC):
    @abstractmethod
    def get_file_study(self) -> FileStudy:
        pass

    @override
    def get_layers(self) -> Sequence[Layer]:
        file_study = self.get_file_study()
        area_ids = list(file_study.config.areas)
        ui_info_map = self._get_ui_info_map(file_study, area_ids)
        layers = file_study.tree.get(["layers", "layers", "layers"])
        if not layers:
            layers[DEFAULT_LAYER_ID] = DEFAULT_LAYER_NAME
        return [
            Layer(
                id=str(layer),
                name=layers[str(layer)],
                areas=[
                    area
                    for area in ui_info_map
                    if str(layer) in self._get_area_layers(ui_info_map, area)
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
    def delete_layer(self, layer_id: str) -> None:
        file_study = self.get_file_study()

        layers = file_study.tree.get(["layers", "layers", "layers"])

        del layers[layer_id]

        file_study.tree.save(layers, ["layers", "layers", "layers"])

    @override
    def layer_exists(self, layer_id: str) -> bool:
        file_study = self.get_file_study()
        layers = file_study.tree.get(["layers", "layers", "layers"])
        return layer_id in layers

    @staticmethod
    def _get_ui_info_map(file_study: FileStudy, area_ids: Sequence[str]) -> dict[str, Any]:
        """
        Get the UI information (a JSON object) for each selected Area.

        Args:
            file_study: A file study from which the configuration can be read.
            area_ids: List of selected area IDs.

        Returns:
            Dictionary where keys are IDs, and values are UI objects.

        Raises:
            ChildNotFoundError: if one of the Area IDs is not found in the configuration.
        """
        # If there is no ID, it is better to return an empty dictionary
        # instead of raising an obscure exception.
        if not area_ids:
            return {}

        ui_info_map = file_study.tree.get(["input", "areas", ",".join(area_ids), "ui"])

        # If there is only one ID in the `area_ids`, the result returned from
        # the `file_study.tree.get` call will be a single UI object.
        # On the other hand, if there are multiple values in `area_ids`,
        # the result will be a dictionary where the keys are the IDs,
        # and the values are the corresponding UI objects.
        if len(area_ids) == 1:
            ui_info_map = {area_ids[0]: ui_info_map}

        # Convert to AreaUIFileData to ensure that the UI object is valid.
        ui_info_map = {area_id: AreaUIFileData(**ui_info).to_config() for area_id, ui_info in ui_info_map.items()}

        return ui_info_map

    @staticmethod
    def _get_area_layers(area_uis: dict[str, Any], area: str) -> list[str]:
        if area in area_uis and "ui" in area_uis[area] and "layers" in area_uis[area]["ui"]:
            return re.split(r"\s+", (str(area_uis[area]["ui"]["layers"]) or ""))
        return []
