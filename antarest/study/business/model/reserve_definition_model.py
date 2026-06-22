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

from typing import Annotated, Any, NewType, TypeAlias

from pydantic import ConfigDict, Field, model_validator
from pydantic.alias_generators import to_camel

from antarest.core.exceptions import ReservedReserveDefinitionId
from antarest.core.serde import AntaresBaseModel
from antarest.study.business.enum_ignore_case import EnumIgnoreCase
from antarest.study.storage.rawstudy.model.filesystem.config.identifier import transform_name_to_id
from antarest.study.storage.rawstudy.model.filesystem.config.validation import ItemName

AreaId: TypeAlias = str
ReserveDefinitionId = NewType("ReserveDefinitionId", str)

GLOBAL_PARAMETERS_SECTION = "globalparameters"

# Reserved reserve ids:
# - "global-parameters": collides with the /areas/{id}/reserves/global-parameters route.
# - GLOBAL_PARAMETERS_SECTION: collides with the [globalparameters] YAML section.
# - "reserves": collides with the `reserves.yml` file at `input/reserves/<area>/reserves`.
_RESERVED_RESERVE_IDS = frozenset({"global-parameters", GLOBAL_PARAMETERS_SECTION, "reserves"})


class ReserveType(EnumIgnoreCase):
    """
    Type of a reserve: up (raise production) or down (lower production).
    """

    UP = "up"
    DOWN = "down"


Cost = Annotated[float, Field(ge=0)]
Ratio = Annotated[float, Field(ge=0, le=1)]
Duration = Annotated[int, Field(ge=0)]


def _check_not_reserved_id(name: str) -> None:
    if transform_name_to_id(name) in _RESERVED_RESERVE_IDS:
        raise ReservedReserveDefinitionId(name)


class ReserveDefinition(AntaresBaseModel):
    model_config = ConfigDict(alias_generator=to_camel, extra="forbid", populate_by_name=True)

    @model_validator(mode="before")
    @classmethod
    def set_id(cls, data: Any) -> Any:
        if isinstance(data, dict) and "id" not in data and "name" in data:
            data["id"] = transform_name_to_id(data["name"])
        return data

    id: str
    name: ItemName
    type: ReserveType
    failure_cost: Cost = 0.0
    spillage_cost: Cost = 0.0
    reference_activation_duration: Duration = 1
    power_activation_ratio: Ratio = 0.0
    energy_activation_ratio: Ratio = 1.0


class ReserveDefinitionCreation(AntaresBaseModel):
    model_config = ConfigDict(alias_generator=to_camel, extra="forbid", populate_by_name=True)

    name: ItemName
    type: ReserveType
    failure_cost: Cost | None = None
    spillage_cost: Cost | None = None
    reference_activation_duration: Duration | None = None
    power_activation_ratio: Ratio | None = None
    energy_activation_ratio: Ratio | None = None

    @model_validator(mode="after")
    def _check_id(self) -> "ReserveDefinitionCreation":
        _check_not_reserved_id(self.name)
        return self


class ReserveDefinitionUpdate(AntaresBaseModel):
    model_config = ConfigDict(alias_generator=to_camel, extra="forbid", populate_by_name=True)

    type: ReserveType | None = None
    failure_cost: Cost | None = None
    spillage_cost: Cost | None = None
    reference_activation_duration: Duration | None = None
    power_activation_ratio: Ratio | None = None
    energy_activation_ratio: Ratio | None = None


ReserveDefinitionUpdates = dict[AreaId, dict[ReserveDefinitionId, ReserveDefinitionUpdate]]


def create_reserve_definition(data: ReserveDefinitionCreation) -> ReserveDefinition:
    return ReserveDefinition.model_validate(data.model_dump(exclude_none=True))


def update_reserve_definition(reserve: ReserveDefinition, data: ReserveDefinitionUpdate) -> ReserveDefinition:
    return reserve.model_copy(update=data.model_dump(exclude_none=True))
