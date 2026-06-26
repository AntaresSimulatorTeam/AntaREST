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
from antarest.study.business.model.reserve_definition_model import ReserveDefinitionId
from antarest.study.business.model.thermal_reserve_certification_model import ThermalReserveCertification
from antarest.study.storage.rawstudy.model.filesystem.config.identifier import transform_name_to_id


def parse_thermal_reserves_certifications(
    data: dict[str, Any],
) -> dict[str, dict[ReserveDefinitionId, ThermalReserveCertification]]:
    result: dict[str, dict[ReserveDefinitionId, ThermalReserveCertification]] = {}
    for content in data.get("participations", []):
        thermal_id = transform_name_to_id(content["cluster"])
        if thermal_id in result:
            raise ValueError(f"Duplicate thermal cluster id: {thermal_id}")
        result[thermal_id] = {}
        for certification in content["certifications"]:
            reserve_id = ReserveDefinitionId(transform_name_to_id(certification.pop("reserve")))
            model = ThermalReserveCertification.model_validate(certification)
            result[thermal_id][reserve_id] = model

    return result


class ThermalClusterReserveParticipationFileData(AntaresBaseModel):
    model_config = ConfigDict(alias_generator=to_kebab_case, extra="forbid", populate_by_name=True)

    reserve: str
    max_power: float
    max_power_off: float
    participation_cost: float
    participation_cost_off: float


def serialize_thermal_reserve_certifications(
    data: dict[ReserveDefinitionId, ThermalReserveCertification],
) -> list[dict[str, Any]]:
    result = []
    for reserve_id, certification in data.items():
        content = {**certification.model_dump(), "reserve": reserve_id}
        result.append(ThermalClusterReserveParticipationFileData.model_validate(content).model_dump(by_alias=True))
    return result
