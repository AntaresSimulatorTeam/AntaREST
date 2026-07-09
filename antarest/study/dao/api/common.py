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
from antarest.study.business.model.reserve_definition_model import ReserveDefinitionId
from antarest.study.business.model.reserve_symmetries_model import ReserveSymmetries


def remove_reserve_symmetries_by_cascade(
    symmetries_dict: dict[str, ReserveSymmetries], reserve_ids_to_remove: set[ReserveDefinitionId]
) -> dict[str, ReserveSymmetries] | None:
    """
    When removing a reserve, we should also remove it from the symmetries.

    Returns:
        The updated symmetries dictionary or None if no symmetries were updated.
    """
    should_update_symmetries = False
    for symmetries in symmetries_dict.values():
        for i, symmetry in enumerate(symmetries):
            symmetries[i] = [reserve_id for reserve_id in symmetry if reserve_id not in reserve_ids_to_remove]
            if len(symmetries[i]) != len(symmetry):
                should_update_symmetries = True
            if len(symmetries[i]) == 1:
                # We only have one reserve left in the symmetry, we should remove it
                symmetries[i] = []
    if should_update_symmetries:
        return symmetries_dict
    return None
