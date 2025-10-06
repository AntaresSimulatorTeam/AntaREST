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
from typing import List, Optional

from pydantic import ConfigDict, Field

from antarest.core.serde import AntaresBaseModel
from antarest.core.utils.string import to_camel_case
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


class AreaUI(AntaresBaseModel):
    """
    Area UI properties for a specific layer.
    """

    model_config = ConfigDict(alias_generator=to_camel_case, populate_by_name=True, extra="forbid")

    x: int = Field(description="X position")
    y: int = Field(description="Y position")
    color_rgb: tuple[int, int, int] = Field(description="RGB color")


class AreaUIUpdate(AntaresBaseModel):
    """
    Partial update for Area UI properties.
    """

    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    x: Optional[int] = None
    y: Optional[int] = None
    color_rgb: Optional[tuple[int, int, int]] = Field(default=None, alias="colorRgb")
