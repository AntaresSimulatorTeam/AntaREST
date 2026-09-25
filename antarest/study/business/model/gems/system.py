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
from typing import Any, List

from pydantic import ConfigDict, model_validator

from antarest.core.serde import AntaresBaseModel
from antarest.core.utils.string import to_kebab_case


class _GemsParameters(AntaresBaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="forbid", alias_generator=to_kebab_case)

    id: str
    time_dependent: bool
    scenario_dependent: bool
    value: float  # TODO: authorize string values when time_dependent and/or scenario_dempendant is True

    @model_validator(mode="after")
    def check_value(self) -> "_GemsParameters":
        if self.time_dependent or self.scenario_dependent:
            raise ValueError("time_dependent and scenario_dependent are not supported yet")
        return self


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


class GemsSystem(AntaresBaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="forbid", alias_generator=to_kebab_case)

    id: str
    description: str | None = None
    model_libraries: list[str] | None = None
    components: List[GemsComponent]
    connections: list[dict[str, Any]] | None = None
    area_connections: list[dict[str, Any]] | None = None
