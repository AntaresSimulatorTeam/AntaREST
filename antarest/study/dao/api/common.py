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
from collections.abc import Collection
from typing import TYPE_CHECKING

from antarest.core.exceptions import (
    AreaNotFound,
    ReserveCertificationNotFound,
    ReserveCertificationsNotFound,
    ReserveDefinitionNotFound,
    STStorageNotFound,
    ThermalClusterNotFound,
)
from antarest.study.business.model.reserve_definition_model import ReserveDefinitionId
from antarest.study.business.model.reserve_symmetries_model import ReserveSymmetries
from antarest.study.dao.common import (
    HydroReserveSymmetriesMapping,
    STStorageReserveSymmetriesMapping,
    ThermalReserveSymmetriesMapping,
)

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
        if not (any(symmetry for symmetry in value.values())):
            continue

        if area_id not in existing_certifications:
            # Means that either the area does not exist, or the area does not contain any thermal certification.
            existing_area_ids = study_dao.get_all_area_ids()
            if area_id not in existing_area_ids:
                raise AreaNotFound(area_id)
            raise ReserveCertificationsNotFound(area_id, "thermal")

        # Verify that the thermals are certified on the reserves they are symmetric on
        for thermal_id, symmetries in value.items():
            for symmetry in symmetries:
                for reserve_id in symmetry:
                    if reserve_id not in existing_certifications[area_id]:
                        if not study_dao.reserve_definition_exists(area_id, reserve_id):
                            raise ReserveDefinitionNotFound(area_id, reserve_id)
                        raise ReserveCertificationNotFound(area_id, "thermal", thermal_id, {reserve_id})
                    if thermal_id not in existing_certifications[area_id][reserve_id]:
                        if not study_dao.thermal_exists(area_id, thermal_id):
                            raise ThermalClusterNotFound(area_id, thermal_id)
                        raise ReserveCertificationNotFound(area_id, "thermal", thermal_id, {reserve_id})


def check_st_storage_symmetries_integrity(
    study_dao: "StudyDao", new_symmetries: STStorageReserveSymmetriesMapping
) -> None:
    existing_certifications = {}
    if len(new_symmetries) == 1:
        # Fetch the given area only to speed up the query
        area_id = next(iter(new_symmetries))
        if certifications_for_area := study_dao.get_st_storage_reserve_certifications(area_id):
            existing_certifications = {area_id: certifications_for_area}
    else:
        existing_certifications = study_dao.get_all_st_storage_reserve_certifications()

    for area_id, value in new_symmetries.items():
        # Handle the case where no symmetries are given. Means we only want to clear them all.
        if not (any(symmetry for symmetry in value.values())):
            continue

        if area_id not in existing_certifications:
            # Means that either the area does not exist, or the area does not contain any st-storage certification.
            existing_area_ids = study_dao.get_all_area_ids()
            if area_id not in existing_area_ids:
                raise AreaNotFound(area_id)
            raise ReserveCertificationsNotFound(area_id, "st-storage")

        # Verify that the st-storages are certified on the reserves they are symmetric on
        for st_storage_id, symmetries in value.items():
            for symmetry in symmetries:
                for reserve_id in symmetry:
                    if reserve_id not in existing_certifications[area_id]:
                        if not study_dao.reserve_definition_exists(area_id, reserve_id):
                            raise ReserveDefinitionNotFound(area_id, reserve_id)
                        raise ReserveCertificationNotFound(area_id, "st-storage", st_storage_id, {reserve_id})
                    if st_storage_id not in existing_certifications[area_id][reserve_id]:
                        if not study_dao.st_storage_exists(area_id, st_storage_id):
                            raise STStorageNotFound(area_id, st_storage_id)
                        raise ReserveCertificationNotFound(area_id, "st-storage", st_storage_id, {reserve_id})


def check_hydro_symmetries_integrity(study_dao: "StudyDao", new_symmetries: HydroReserveSymmetriesMapping) -> None:
    existing_certifications = {}
    if len(new_symmetries) == 1:
        # Fetch the given area only to speed up the query
        area_id = next(iter(new_symmetries))
        if certifications_for_area := study_dao.get_hydro_reserve_certifications(area_id):
            existing_certifications = {area_id: certifications_for_area}
    else:
        existing_certifications = study_dao.get_all_hydro_reserve_certifications()

    for area_id, symmetries in new_symmetries.items():
        # Handle the case where no symmetries are given. Means we only want to clear them all.
        if not (any(symmetry for symmetry in symmetries)):
            continue

        if area_id not in existing_certifications:
            # Means that either the area does not exist, or the area does not contain any hydro certification.
            existing_area_ids = study_dao.get_all_area_ids()
            if area_id not in existing_area_ids:
                raise AreaNotFound(area_id)
            raise ReserveCertificationsNotFound(area_id, "hydro")

        # Verify that the long-term storage is certified on the reserves it is symmetric on.
        # There is no asset id here: an area owns exactly one long-term storage.
        for symmetry in symmetries:
            for reserve_id in symmetry:
                if reserve_id not in existing_certifications[area_id]:
                    if not study_dao.reserve_definition_exists(area_id, reserve_id):
                        raise ReserveDefinitionNotFound(area_id, reserve_id)
                    raise ReserveCertificationNotFound(area_id, "hydro", None, {reserve_id})


def remove_reserves_from_symmetries(
    symmetries: ReserveSymmetries, reserves_to_remove: Collection[ReserveDefinitionId]
) -> bool:
    """
    When removing a reserve, we should also remove it from the symmetries.

    A symmetry left with less than 2 reserves is meaningless, so it is dropped altogether.
    The given symmetries are updated in place.

    Returns:
        Whether the symmetries were modified.
    """
    kept = []
    for symmetry in symmetries:
        new_symmetry = [reserve_id for reserve_id in symmetry if reserve_id not in reserves_to_remove]
        # A symmetry holding a single reserve is meaningless, so it is not kept.
        if len(new_symmetry) > 1:
            kept.append(new_symmetry)

    if kept == symmetries:
        return False
    symmetries[:] = kept
    return True


def remove_reserves_from_symmetries_dict(
    symmetries_dict: dict[str, ReserveSymmetries],
    reserves_to_remove: dict[str, set[ReserveDefinitionId]] | set[ReserveDefinitionId],
) -> dict[str, ReserveSymmetries] | None:
    """
    When removing a reserve, we should also remove it from the symmetries of every asset.

    `reserves_to_remove` is either the same set for every asset, or one set per asset.

    Returns:
        The updated symmetries dictionary or None if no symmetries were updated.
    """
    should_update_symmetries = False
    for object_id, symmetries in symmetries_dict.items():
        reserves = (
            reserves_to_remove.get(object_id, set()) if isinstance(reserves_to_remove, dict) else reserves_to_remove
        )
        should_update_symmetries |= remove_reserves_from_symmetries(symmetries, reserves)
    if should_update_symmetries:
        return symmetries_dict
    return None
