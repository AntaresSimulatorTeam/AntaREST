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
from typing import Any

from pydantic import ConfigDict

from antarest.core.serde import AntaresBaseModel
from antarest.core.utils.string import to_kebab_case
from antarest.study.business.model.reserve_definition_model import ReserveDefinition, ReserveType


class ReserveDefinitionFileData(AntaresBaseModel):
    model_config = ConfigDict(alias_generator=to_kebab_case, extra="forbid", populate_by_name=True)

    name: str
    type: ReserveType
    failure_cost: float = 0.0
    spillage_cost: float = 0.0
    reference_activation_duration: int = 1
    power_activation_ratio: float = 0.0
    energy_activation_ratio: float = 1.0

    def to_model(self) -> ReserveDefinition:
        return ReserveDefinition.model_validate(self.model_dump())

    @classmethod
    def from_model(cls, reserve: ReserveDefinition) -> "ReserveDefinitionFileData":
        return cls.model_validate(reserve.model_dump(exclude={"id"}))


def parse_reserve_definition(data: dict[str, Any]) -> ReserveDefinition:
    return ReserveDefinitionFileData.model_validate(data).to_model()


def serialize_reserve_definitions(reserves: list[ReserveDefinition]) -> list[dict[str, Any]]:
    return [
        ReserveDefinitionFileData.from_model(reserve).model_dump(mode="json", by_alias=True) for reserve in reserves
    ]
