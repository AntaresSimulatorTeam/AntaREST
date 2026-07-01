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

Cost = Annotated[float, Field(ge=0)]
Power = Annotated[float, Field(ge=0)]

##########################
# Thermal part
##########################


class ThermalReserveCertification(AntaresBaseModel):
    model_config = ConfigDict(alias_generator=to_camel, extra="forbid", populate_by_name=True)

    max_power: Power = 0.0
    max_power_off: Power = 0.0
    participation_cost: Cost = 0.0
    participation_cost_off: Cost = 0.0


ThermalId: TypeAlias = str
ThermalReserveCertificationMapping = dict[ReserveDefinitionId, dict[ThermalId, ThermalReserveCertification]]


##########################
# Whole model
##########################


class ReserveCertifications(AntaresBaseModel):
    model_config = ConfigDict(alias_generator=to_camel, extra="forbid", populate_by_name=True)

    thermals: ThermalReserveCertificationMapping
