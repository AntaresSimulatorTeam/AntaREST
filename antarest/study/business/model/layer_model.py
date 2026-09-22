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

from pydantic import ConfigDict

from antarest.core.serde import AntaresBaseModel
from antarest.core.utils.string import to_camel_case


class Layer(AntaresBaseModel):
    model_config = ConfigDict(alias_generator=to_camel_case, populate_by_name=True, extra="forbid")

    id: str
    name: str
    areas: list[str] = []


class LayerCreation(AntaresBaseModel):
    model_config = ConfigDict(alias_generator=to_camel_case, populate_by_name=True, extra="forbid")

    id: str | None = None
    name: str


class LayerUpdate(AntaresBaseModel):
    model_config = ConfigDict(alias_generator=to_camel_case, populate_by_name=True, extra="forbid")

    id: str
    name: str | None = None
    areas: list[str] | None = None


def create_layer(current_layers: list[Layer], layer: LayerCreation) -> Layer:
    # Use the provided ID if available, otherwise calculate the next available ID
    if layer.id is not None:
        new_id = layer.id
    else:
        new_id = str(
            max(
                (int(existing_layer.id) for existing_layer in current_layers if existing_layer.id is not None),
                default=0,
            )
            + 1
        )
    return Layer(id=new_id, name=layer.name)


def update_layer_name(layers: list[Layer], data: LayerUpdate) -> Layer:
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
