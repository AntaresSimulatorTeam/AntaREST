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
from typing import Annotated, TypeAlias

from pydantic import ConfigDict, Field
from pydantic.alias_generators import to_camel

from antarest.core.serde import AntaresBaseModel
from antarest.study.business.model.reserve_definition_model import ReserveDefinitionId

AreaId: TypeAlias = str
ThermalId: TypeAlias = str

Cost = Annotated[float, Field(ge=0)]
Power = Annotated[float, Field(ge=0)]


class ThermalReserveCertification(AntaresBaseModel):
    model_config = ConfigDict(alias_generator=to_camel, extra="forbid", populate_by_name=True)

    max_power: Power = 0.0
    max_power_off: Power = 0.0
    participation_cost: Cost = 0.0
    participation_cost_off: Cost = 0.0


class ThermalReserveCertificationCreation(AntaresBaseModel):
    model_config = ConfigDict(alias_generator=to_camel, extra="forbid", populate_by_name=True)

    max_power: Power | None = None
    max_power_off: Power | None = None
    participation_cost: Cost | None = None
    participation_cost_off: Cost | None = None


class ThermalReserveCertificationUpdate(AntaresBaseModel):
    model_config = ConfigDict(alias_generator=to_camel, extra="forbid", populate_by_name=True)

    max_power: Power | None = None
    max_power_off: Power | None = None
    participation_cost: Cost | None = None
    participation_cost_off: Cost | None = None


# Update map: area -> thermal -> reserve -> update
ThermalReserveCertificationUpdates = dict[
    AreaId, dict[ThermalId, dict[ReserveDefinitionId, ThermalReserveCertificationUpdate]]
]


def create_thermal_reserve_certification(
    data: ThermalReserveCertificationCreation,
) -> ThermalReserveCertification:
    return ThermalReserveCertification.model_validate(data.model_dump(exclude_none=True))


def update_thermal_reserve_certification(
    certification: ThermalReserveCertification,
    data: ThermalReserveCertificationUpdate,
) -> ThermalReserveCertification:
    return certification.model_copy(update=data.model_dump(exclude_none=True))