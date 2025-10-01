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

import enum
from typing import List, Mapping, Optional, Sequence

from pydantic import Field

from antarest.core.serde import AntaresBaseModel
from antarest.study.business.model.thermal_cluster_model import ThermalCluster


class AreaType(enum.Enum):
    AREA = "AREA"
    DISTRICT = "DISTRICT"


class Area(AntaresBaseModel):
    id: str
    name: str
    thermals: Optional[List[ThermalCluster]] = None


class AreaCreation(AntaresBaseModel):
    name: str
    type: Optional[AreaType] = Field(
        default=None,
        json_schema_extra={"deprecated": True},
    )


class UpdateAreaUi(AntaresBaseModel, extra="forbid", populate_by_name=True):
    x: int = Field(title="X position")
    y: int = Field(title="Y position")
    color_rgb: Sequence[int] = Field(title="RGB color", alias="colorRgb")
    layer_x: Mapping[int, int] = Field(default_factory=dict, title="X position of each layer", alias="layerX")
    layer_y: Mapping[int, int] = Field(default_factory=dict, title="Y position of each layer", alias="layerY")
    layer_color: Mapping[int, str] = Field(default_factory=dict, title="Color of each layer", alias="layerColor")
