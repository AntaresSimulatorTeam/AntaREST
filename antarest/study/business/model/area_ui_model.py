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
from typing import Dict, Set

from pydantic import ConfigDict, Field

from antarest.core.serde import AntaresBaseModel
from antarest.core.utils.string import to_camel_case


class UI:
    model_config = ConfigDict(alias_generator=to_camel_case, populate_by_name=True, extra="forbid")

    x: int
    y: int
    color_r: int = Field(ge=0, le=255)
    color_g: int = Field(ge=0, le=255)
    color_b: int = Field(ge=0, le=255)
    layers: Set[str] = Field(default_factory=set)

class UIUpdate(AntaresBaseModel):
    model_config = ConfigDict(alias_generator=to_camel_case, populate_by_name=True, extra="forbid")

    x: int | None = None
    y: int | None = None
    color_r: int | None = Field(None, ge=0, le=255)
    color_g: int | None = Field(None, ge=0, le=255)
    color_b: int | None = Field(None, ge=0, le=255)
    layers: Set[str] | None = None


class LayerCoordinate(AntaresBaseModel):
    model_config = ConfigDict(alias_generator=to_camel_case, populate_by_name=True, extra="forbid")

    coordinates: Dict[str, int] = Field(default_factory=dict)


class LayerCoordinateUpdate(AntaresBaseModel):
    model_config = ConfigDict(alias_generator=to_camel_case, populate_by_name=True, extra="forbid")

    coordinates: Dict[str, int] | None = None


class LayerColor(AntaresBaseModel):
    model_config = ConfigDict(alias_generator=to_camel_case, populate_by_name=True, extra="forbid")

    colors: Dict[str, str] = Field(default_factory=dict)


class LayerColorUpdate(AntaresBaseModel):
    model_config = ConfigDict(alias_generator=to_camel_case, populate_by_name=True, extra="forbid")

    colors: Dict[str, str] | None = None


class AreaUI:
    model_config = ConfigDict(alias_generator=to_camel_case, populate_by_name=True, extra="forbid")

    ui: UI
    layer_x: LayerCoordinate
    layer_y: LayerCoordinate
    layer_color: LayerColor


class AreaUIUpdate(AntaresBaseModel):
    model_config = ConfigDict(alias_generator=to_camel_case, populate_by_name=True, extra="forbid")

    ui: UIUpdate | None = None
    layer_x: LayerCoordinateUpdate | None = None
    layer_y: LayerCoordinateUpdate | None = None
    layer_color: LayerColorUpdate | None = None






