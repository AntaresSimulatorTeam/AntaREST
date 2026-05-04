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

from typing import Annotated, NewType, TypeAlias

from pydantic import ConfigDict, Field
from pydantic.alias_generators import to_camel

from antarest.core.serde import AntaresBaseModel
from antarest.study.business.model.reserve_definition_model import ReserveDefinitionId
from antarest.study.storage.rawstudy.model.filesystem.config.validation import ItemName

AreaId: TypeAlias = str
ThermalId: TypeAlias = str
ThermalClusterReserveParticipationId = NewType("ThermalClusterReserveParticipationId", str)

Cost = Annotated[float, Field(ge=0)]
Power = Annotated[float, Field(ge=0)]


class ThermalClusterReserveParticipation(AntaresBaseModel):
    """
    Parameters describing a thermal cluster's participation to a reserve.

    A participation is identified by the ``(area_id, thermal_id, id)`` triplet, where
    ``id`` is the reserve identifier. The cluster identity is carried by the URL/context
    rather than embedded in the entity itself: the INI file format does need a
    ``cluster-name`` field, but that field is auto-populated at serialization time from
    the ``thermal_id`` of the cluster and is therefore not part of the canonical model.
    """

    model_config = ConfigDict(alias_generator=to_camel, extra="forbid", populate_by_name=True)

    id: ItemName
    max_power: Power = 0.0
    max_power_off: Power = 0.0
    participation_cost: Cost = 0.0
    participation_cost_off: Cost = 0.0


class ThermalClusterReserveParticipationCreation(AntaresBaseModel):
    model_config = ConfigDict(alias_generator=to_camel, extra="forbid", populate_by_name=True)

    id: ItemName
    max_power: Power | None = None
    max_power_off: Power | None = None
    participation_cost: Cost | None = None
    participation_cost_off: Cost | None = None


class ThermalClusterReserveParticipationUpdate(AntaresBaseModel):
    model_config = ConfigDict(alias_generator=to_camel, extra="forbid", populate_by_name=True)

    max_power: Power | None = None
    max_power_off: Power | None = None
    participation_cost: Cost | None = None
    participation_cost_off: Cost | None = None


# Update map: area -> thermal -> reserve -> update
ThermalClusterReserveParticipationUpdates = dict[
    AreaId, dict[ThermalId, dict[ReserveDefinitionId, ThermalClusterReserveParticipationUpdate]]
]


def create_thermal_cluster_reserve_participation(
    data: ThermalClusterReserveParticipationCreation,
) -> ThermalClusterReserveParticipation:
    return ThermalClusterReserveParticipation.model_validate(data.model_dump(exclude_none=True))


def update_thermal_cluster_reserve_participation(
    participation: ThermalClusterReserveParticipation,
    data: ThermalClusterReserveParticipationUpdate,
) -> ThermalClusterReserveParticipation:
    return participation.model_copy(update=data.model_dump(exclude_none=True))
