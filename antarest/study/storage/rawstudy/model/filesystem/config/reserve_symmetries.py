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

from antarest.study.business.model.reserve_definition_model import ReserveDefinitionId
from antarest.study.business.model.reserve_symmetries_model import ReserveSymmetries
from antarest.study.storage.rawstudy.model.filesystem.config.identifier import transform_name_to_id


def parse_thermal_reserves_symmetries(data: dict[str, Any]) -> dict[str, ReserveSymmetries]:
    result: dict[str, ReserveSymmetries] = {}
    for content in data.get("participations", []):
        thermal_id = transform_name_to_id(content["cluster"])
        if thermal_id in result:
            raise ValueError(f"Duplicate thermal cluster id: {thermal_id}")
        for symmetry in content.get("symmetries", []):
            reserve_ids = [ReserveDefinitionId(s) for s in symmetry["reserves"]]
            result.setdefault(thermal_id, []).append(reserve_ids)

    return result


def serialize_reserve_symmetries(symmetries: ReserveSymmetries) -> list[dict[str, Any]]:
    if symmetries == [[]]:
        return []
    return [{"reserves": symmetry} for symmetry in symmetries]
