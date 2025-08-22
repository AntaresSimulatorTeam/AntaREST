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
from typing import Dict

from pydantic import ConfigDict, Field

from antarest.core.serde import AntaresBaseModel
from antarest.core.utils.string import to_kebab_case


class UIFileData(AntaresBaseModel):
    """
    UI properties for serialization in ini file.
    Represents the [ui] section of area configuration.
    """
    model_config = ConfigDict(alias_generator=to_kebab_case, populate_by_name=True, extra="forbid")

    x: int
    y: int
    color_r: int = Field(ge=0, le=255)
    color_g: int = Field(ge=0, le=255)
    color_b: int = Field(ge=0, le=255)
    layers: str  # Format: "0 1" (space-separated layer IDs)


class LayerXFileData(AntaresBaseModel):
    """
    LayerX coordinates for serialization in ini file.
    Represents the [layerX] section.
    """
    model_config = ConfigDict(alias_generator=to_kebab_case, populate_by_name=True, extra="forbid")

    # Dict where key is layer ID and value is X coordinate
    # Example: {"0": "-266", "1": "-78"}
    coordinates: Dict[str, str] = Field(default_factory=dict)


class LayerYFileData(AntaresBaseModel):
    """
    LayerY coordinates for serialization in ini file.
    Represents the [layerY] section.
    """
    model_config = ConfigDict(alias_generator=to_kebab_case, populate_by_name=True, extra="forbid")

    # Dict where key is layer ID and value is Y coordinate
    # Example: {"0": "164", "1": "133"}
    coordinates: Dict[str, str] = Field(default_factory=dict)


class LayerColorFileData(AntaresBaseModel):
    """
    LayerColor data for serialization in ini file.
    Represents the [layerColor] section.
    """
    model_config = ConfigDict(alias_generator=to_kebab_case, populate_by_name=True, extra="forbid")

    # Dict where key is layer ID and value is color in "r,g,b" format
    # Example: {"0": "255,245,0", "1": "230,108,44"}
    colors: Dict[str, str] = Field(default_factory=dict)


class AreaUIFileData(AntaresBaseModel):
    """
    Complete area UI data for ini file serialization.
    Contains all sections: [ui], [layerX], [layerY], [layerColor]
    """
    model_config = ConfigDict(alias_generator=to_kebab_case, populate_by_name=True, extra="forbid")

    ui: UIFileData
    layer_x: LayerXFileData = Field(alias="layerX")
    layer_y: LayerYFileData = Field(alias="layerY")
    layer_color: LayerColorFileData = Field(alias="layerColor")
