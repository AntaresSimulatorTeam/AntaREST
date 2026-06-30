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

from pydantic import BeforeValidator, ConfigDict
from pydantic.alias_generators import to_camel

from antarest.core.serde import AntaresBaseModel
from antarest.study.business.model.reserve_definition_model import ReserveDefinitionId


def _symmetry_validator(data: list[str]) -> list[str]:
    if len(data) < 2:
        raise ValueError(f"Reserve symmetries should have at least 2 elements, and was {data}")
    if len(set(data)) != len(data):
        raise ValueError(f"Reserve symmetries should not contain duplicates, and was {data}")
    return data


ReserveSymmetry: TypeAlias = Annotated[list[ReserveDefinitionId], BeforeValidator(_symmetry_validator)]


ThermalId: TypeAlias = str
StStorageId: TypeAlias = str
AreaId: TypeAlias = str


class ReserveSymmetries(AntaresBaseModel):
    model_config = ConfigDict(alias_generator=to_camel, extra="forbid", populate_by_name=True)

    thermals: dict[ThermalId, list[ReserveSymmetry]] = {}
    st_storages: dict[StStorageId, list[ReserveSymmetry]] = {}
    hydro: dict[AreaId, list[ReserveSymmetry]] = {}


def merge_symmetries(symmetries: list[ReserveSymmetry]) -> list[ReserveSymmetry]:
    """
    The Simulator accepts symmetries to be written as [a, b] and [b, c] separately, even if it means the same thing as [a, b, c].
    This function merges symmetries to have the least number of them.
    """
    if not symmetries:
        return []

    merged_sets = [set(symmetries[0])]
    for symmetry in symmetries[1:]:
        current_set = set(symmetry)
        for merged_set in merged_sets:
            if current_set & merged_set:  # Check for intersection
                merged_set.update(current_set)
                break
        else:
            merged_sets.append(current_set)

    # Replace sets with sorted lists for reproducibility
    return [sorted(list(merged_set)) for merged_set in merged_sets]
