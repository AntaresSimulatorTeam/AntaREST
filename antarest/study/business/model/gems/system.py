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
from enum import StrEnum
from typing import Annotated, List, Self, TypeAlias

from pydantic import ConfigDict, Field, model_validator

from antarest.core.exceptions import (
    GemsInvalidParameterValue,
    GemsParameterValueIsConstantButShouldNotBe,
    GemsParameterValueIsNotConstantButShouldBe,
)
from antarest.core.model import LowerCaseStr
from antarest.core.serde import AntaresBaseModel
from antarest.core.utils.string import to_kebab_case


class GemsParameters(AntaresBaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="forbid", alias_generator=to_kebab_case)

    id: str
    time_dependent: bool
    scenario_dependent: bool
    value: float | str

    def is_dataseries(self) -> bool:
        return self.time_dependent or self.scenario_dependent

    @model_validator(mode="after")
    def validate_value(self) -> "GemsParameters":
        if self.is_dataseries() and not isinstance(self.value, str):
            raise GemsParameterValueIsConstantButShouldNotBe(self.id, self.value)

        if not self.is_dataseries() and not isinstance(self.value, (int, float)):
            raise GemsParameterValueIsNotConstantButShouldBe(self.id, self.value)
        return self

    def get_value_as_float(self) -> float:

        if self.is_dataseries():
            raise GemsInvalidParameterValue(f"Trying to get a float value from a dataseries for parameter {self.id}")

        return float(self.value)

    def get_value_as_str(self) -> str:
        if not self.is_dataseries():
            raise GemsInvalidParameterValue(f"Trying to get a string value from a constant for parameter {self.id}")

        return str(self.value)


class _GemsProperties(AntaresBaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="forbid", alias_generator=to_kebab_case)

    id: str
    value: str


class IntegerStrategyId(StrEnum):
    EXACT = "exact"
    RELAXED = "relaxed"
    HEURISTIC = "heuristic"


class IntegerStrategyHeuristicId(StrEnum):
    FAST = "fast"
    ACCURATE = "accurate"


class _IntegerStrategy(AntaresBaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="forbid", alias_generator=to_kebab_case)

    id: IntegerStrategyId
    heuristic_id: IntegerStrategyHeuristicId | None = None

    @model_validator(mode="after")
    def validate_integer_strategy(self) -> Self:
        if self.id == IntegerStrategyId.HEURISTIC and self.heuristic_id is None:
            raise ValueError("heuristic-id is required when id is 'heuristic'")

        if self.heuristic_id is not None and self.id != IntegerStrategyId.HEURISTIC:
            raise ValueError("heuristic-id is forbidden when id is not 'heuristic'")

        return self


_MODEL_ID_REGEX = r"^[a-z0-9_-]+\.[a-z0-9_-]+$"  # library_id.model_id
ModelId: TypeAlias = Annotated[str, Field(pattern=_MODEL_ID_REGEX)]


def split_library_and_model_id(model_id: ModelId) -> tuple[str, str]:
    library_id, model_id = model_id.split(".", maxsplit=1)
    return library_id, model_id


class GemsComponent(AntaresBaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="forbid", alias_generator=to_kebab_case)

    id: str
    model: ModelId
    scenario_group: str | None = None
    integer_strategy: _IntegerStrategy | None = None
    parameters: List[GemsParameters] = []
    properties: List[_GemsProperties] = []


class GemsComponentConnection(AntaresBaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="forbid", alias_generator=to_kebab_case, frozen=True)

    component1: str
    component2: str
    port1: str
    port2: str


class GemsAreaConnection(AntaresBaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="forbid", alias_generator=to_kebab_case)

    component: str
    port: str
    # Antares Simulator lowercases the area before matching it against the legacy area ids
    area: LowerCaseStr


class _GemsThermalComponent(AntaresBaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="forbid", alias_generator=to_kebab_case)

    # Antares Simulator lowercases the area, but matches the cluster id exactly
    area: LowerCaseStr
    cluster_id: str


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
