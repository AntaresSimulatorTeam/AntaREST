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

import enum
from typing import Dict, List, Optional

from pydantic import ConfigDict, Field

from antarest.core.serde import AntaresBaseModel
from antarest.core.utils.string import to_camel_case
from antarest.study.business.model.thermal_cluster_model import ThermalCluster

DEFAULT_LAYER_ID = "0"
DEFAULT_LAYER_NAME = "All"


class AreaType(enum.Enum):
    AREA = "AREA"
    DISTRICT = "DISTRICT"


class AreaInfo(AntaresBaseModel):
    """
    Basic information about an area.
    Used for listing areas with their thermal clusters.
    """

    id: str
    name: str
    thermals: Optional[List[ThermalCluster]] = None


class AreaCreation(AntaresBaseModel):
    name: str
    type: Optional[AreaType] = Field(
        default=None,
        json_schema_extra={"deprecated": True},
    )


class AreaUI(AntaresBaseModel):
    """
    Area UI properties for a specific layer.
    """

    model_config = ConfigDict(alias_generator=to_camel_case, populate_by_name=True, extra="forbid")

    x: int = Field(default=0, description="X position")
    y: int = Field(default=0, description="Y position")
    color_rgb: tuple[int, int, int] = Field(default=(230, 108, 44), description="RGB color")


class AreaUIUpdate(AntaresBaseModel):
    """
    Partial update for Area UI properties.
    """

    model_config = ConfigDict(alias_generator=to_camel_case, populate_by_name=True, extra="forbid")

    x: Optional[int] = None
    y: Optional[int] = None
    color_rgb: Optional[tuple[int, int, int]] = None


def update_area_ui(area_ui: AreaUI, data: AreaUIUpdate) -> AreaUI:
    """
    Update area UI properties with partial data.

    Args:
        area_ui: Current area UI properties
        data: Partial update data

    Returns:
        Updated area UI properties
    """
    current_ui = area_ui.model_dump(mode="json")
    new_ui = data.model_dump(mode="json", exclude_none=True)
    current_ui.update(new_ui)
    return AreaUI.model_validate(current_ui)


class AreaUIData(AntaresBaseModel):
    """
    UI data for a single area containing base UI properties and layer-specific data.
    This represents the complete UI configuration for an area across all layers.
    """

    model_config = ConfigDict(populate_by_name=True)

    ui: Dict[str, int | str] = Field(
        default_factory=dict,
        description="Base UI properties with x, y, color_r, color_g, color_b, and layers",
    )
    layer_x: Dict[str, int] = Field(
        default_factory=dict,
        alias="layerX",
        description="X position for each layer",
    )
    layer_y: Dict[str, int] = Field(
        default_factory=dict,
        alias="layerY",
        description="Y position for each layer",
    )
    layer_color: Dict[str, str] = Field(
        default_factory=dict,
        alias="layerColor",
        description="Color string (R, G, B) for each layer",
    )
