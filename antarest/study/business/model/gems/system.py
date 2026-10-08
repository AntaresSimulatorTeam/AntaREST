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

from pydantic import ConfigDict

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


class GemsSystem(AntaresBaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="allow", alias_generator=to_kebab_case)

    id: str
    description: str | None = None
    components: List[GemsComponent]
    connections: List[GemsComponentConnection] = []
    # TODO: add 'area_connections' and 'thermal-capacity-connections' fields
