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
from antarest.study.business.model.thermal_cluster_reserve_participation_model import (
    ThermalClusterReserveParticipation,
)


class ThermalClusterReserveParticipationFileData(AntaresBaseModel):
    model_config = ConfigDict(alias_generator=to_kebab_case, extra="forbid", populate_by_name=True)

    cluster_name: str
    max_power: float = 0.0
    max_power_off: float = 0.0
    participation_cost: float = 0.0
    participation_cost_off: float = 0.0

    def to_model(self, reserve_id: str) -> ThermalClusterReserveParticipation:
        payload = self.model_dump()
        payload.pop("cluster_name", None)
        return ThermalClusterReserveParticipation.model_validate({"id": reserve_id, **payload})

    @classmethod
    def from_model(
        cls, thermal_id: str, participation: ThermalClusterReserveParticipation
    ) -> "ThermalClusterReserveParticipationFileData":
        payload = participation.model_dump(exclude={"id"})
        payload["cluster_name"] = thermal_id
        return cls.model_validate(payload)


def parse_thermal_cluster_reserve_participation(
    reserve_id: str, data: dict[str, Any]
) -> ThermalClusterReserveParticipation:
    return ThermalClusterReserveParticipationFileData.model_validate(data).to_model(reserve_id)


def serialize_thermal_cluster_reserve_participation(
    thermal_id: str, participation: ThermalClusterReserveParticipation
) -> dict[str, Any]:
    return ThermalClusterReserveParticipationFileData.from_model(thermal_id, participation).model_dump(
        mode="json", by_alias=True
    )
