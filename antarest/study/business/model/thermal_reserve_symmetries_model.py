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
from typing import TypeAlias

from antarest.study.business.model.reserve_definition_model import ReserveDefinitionId

AreaId: TypeAlias = str
ThermalId: TypeAlias = str
ThermalReserveSymmetry: TypeAlias = list[ReserveDefinitionId]

# Update map: area -> thermal -> list of reserve ids
ThermalReserveSymmetriesUpdate = dict[AreaId, dict[ThermalId, ThermalReserveSymmetry]]


def merge_symmetries(symmetries: list[ThermalReserveSymmetry]) -> list[ThermalReserveSymmetry]:
    """
    The Simulator accepts symmetries to be written as [a, b] and [b, c] separately, even if it means the same thing as [a, b, c].
    This function merges symmetries to have the least number of them.
    """
    if not symmetries:
        return []

    merged_sets = [set(symmetries[0])]
    for symmetry in symmetries[1:]:
        merged = False
        for reserve_id in symmetry:
            for k, merged_set in enumerate(merged_sets):
                if reserve_id in merged_set:
                    merged_sets[k] = merged_set | set(symmetry)
                    merged = True
                    break
            if merged:
                break
        if not merged:
            merged_sets.append(set(symmetry))

    # Replace sets with lists
    merged_sets = [sorted(list(merged_set)) for merged_set in merged_sets]
    return merged_sets
