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

from pydantic import ConfigDict

from antarest.core.serde import AntaresBaseModel
from antarest.core.utils.string import to_camel_case


class Layer(AntaresBaseModel):
    model_config = ConfigDict(alias_generator=to_camel_case, populate_by_name=True, extra="forbid")

    id: str
    name: str | None = None
    areas: List[str] | None = None


class LayerCreation(AntaresBaseModel):
    model_config = ConfigDict(alias_generator=to_camel_case, populate_by_name=True, extra="forbid")

    name: str


class LayerUpdate(AntaresBaseModel):
    model_config = ConfigDict(alias_generator=to_camel_case, populate_by_name=True, extra="forbid")

    id: str
    name: str | None = None
    areas: List[str] | None = None


def create_layer(current_layers: list[Layer], layer: LayerCreation) -> Layer:
    new_id = max((int(layer.id) for layer in current_layers if layer.id is not None), default=0) + 1
    return Layer(id=str(new_id), name=layer.name)


def update_layer_name(layers: List[Layer], data: LayerUpdate) -> Layer:
    """
    Updates a layer according to the provided update data.
    """
    for layer in layers:
        if layer.id == data.id:
            updated_layer = Layer(
                id=layer.id, name=data.name if data.name is not None else layer.name, areas=layer.areas
            )
            return updated_layer

    raise ValueError(f"Layer with id {data.name} not found")
