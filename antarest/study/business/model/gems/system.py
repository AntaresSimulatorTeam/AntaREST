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
from typing import List

from pydantic import ConfigDict, field_validator

from antarest.core.serde import AntaresBaseModel
from antarest.core.utils.string import to_kebab_case


class _GemsParameters(AntaresBaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="forbid", alias_generator=to_kebab_case)

    id: str
    time_dependent: bool
    scenario_dependent: bool
    value: float  # TODO: authorize string values when time_dependent and/or scenario_dependant is True


class _GemsProperties(AntaresBaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="forbid", alias_generator=to_kebab_case)

    id: str
    value: str


class GemsComponent(AntaresBaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="forbid", alias_generator=to_kebab_case)

    id: str
    model: str
    scenario_group: str | None = None
    parameters: List[_GemsParameters] | None = None
    properties: List[_GemsProperties] | None = None


class GemsComponentConnection(AntaresBaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="forbid", alias_generator=to_kebab_case, frozen=True)

    component1: str
    component2: str
    port1: str
    port2: str


class GemsAreaConnection(AntaresBaseModel):
    """
    Connects a port of a GEMS component to a legacy Antares area.
    """

    model_config = ConfigDict(populate_by_name=True, extra="forbid", alias_generator=to_kebab_case)

    component: str
    port: str
    area: str

    @field_validator("area")
    @classmethod
    def _to_lower(cls, value: str) -> str:
        # Antares Simulator lowercases the area before matching it against the legacy area ids
        return value.lower()


class _GemsThermalComponent(AntaresBaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="forbid", alias_generator=to_kebab_case)

    area: str
    cluster_id: str

    @field_validator("area", "cluster_id")
    @classmethod
    def _to_lower(cls, value: str) -> str:
        # Legacy area and thermal cluster ids are lowercase
        return value.lower()


class GemsThermalCapacityConnection(AntaresBaseModel):
    """
    Connects a port of a GEMS component to a legacy thermal cluster, whose capacity is replaced by the port field.
    """

    model_config = ConfigDict(populate_by_name=True, extra="forbid", alias_generator=to_kebab_case)

    component: str
    port: str
    thermal_component: _GemsThermalComponent


class GemsSystem(AntaresBaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="allow", alias_generator=to_kebab_case)

    id: str
    description: str | None = None
    components: List[GemsComponent]
    connections: List[GemsComponentConnection] = []
    area_connections: List[GemsAreaConnection] = []
    thermal_capacity_connections: List[GemsThermalCapacityConnection] = []
