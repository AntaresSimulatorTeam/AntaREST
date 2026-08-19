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
from typing import TYPE_CHECKING

from antarest.core.exceptions import (
    AreaNotFound,
    ReserveDefinitionNotFound,
    ThermalClusterNotFound,
    ThermalReserveCertificationNotFound,
    ThermalReserveCertificationsNotFound,
)
from antarest.study.business.model.reserve_definition_model import ReserveDefinitionId
from antarest.study.business.model.reserve_symmetries_model import ReserveSymmetries
from antarest.study.dao.common import ThermalReserveSymmetriesMapping

if TYPE_CHECKING:
    from antarest.study.dao.api.study_dao import StudyDao


def check_thermal_symmetries_integrity(study_dao: "StudyDao", new_symmetries: ThermalReserveSymmetriesMapping) -> None:
    existing_certifications = {}
    if len(new_symmetries) == 1:
        # Fetch the given area only to speed up the query
        area_id = next(iter(new_symmetries))
        if certifications_for_area := study_dao.get_thermal_reserve_certifications(area_id):
            existing_certifications = {area_id: certifications_for_area}
    else:
        existing_certifications = study_dao.get_all_thermal_reserve_certifications()

    for area_id, value in new_symmetries.items():
        # Handle the case where no symmetries are given. Means we only want to clear them all.
        if all(symmetries == [[]] for symmetries in value.values()):
            continue

        if area_id not in existing_certifications:
            # Means that either the area does not exist, or the area does not contain any thermal certification.
            existing_area_ids = study_dao.get_all_area_ids()
            if area_id not in existing_area_ids:
                raise AreaNotFound(area_id)
            raise ThermalReserveCertificationsNotFound(area_id)

        # Verify that the thermals are certified on the reserves they are symmetric on
        for thermal_id, symmetries in value.items():
            for symmetry in symmetries:
                for reserve_id in symmetry:
                    if reserve_id not in existing_certifications[area_id]:
                        if not study_dao.reserve_definition_exists(area_id, reserve_id):
                            raise ReserveDefinitionNotFound(area_id, reserve_id)
                        raise ThermalReserveCertificationNotFound(area_id, thermal_id, {reserve_id})
                    if thermal_id not in existing_certifications[area_id][reserve_id]:
                        if not study_dao.thermal_exists(area_id, thermal_id):
                            raise ThermalClusterNotFound(area_id, thermal_id)
                        raise ThermalReserveCertificationNotFound(area_id, thermal_id, {reserve_id})


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
