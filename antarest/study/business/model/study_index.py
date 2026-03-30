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

from collections.abc import Iterable, Mapping

from antarest.study.storage.rawstudy.model.filesystem.config.identifier import transform_name_to_id


class StudyIndex:
    """
    A class containing information about all identifiable objects IDs and names of a study.
    """

    def __init__(
        self,
        areas: Iterable[str],
        links: Iterable[tuple[str, str]],
        thermals: Mapping[str, Iterable[str]],
        storages: Mapping[str, Iterable[str]],
        bc_groups: Iterable[str],
        renewables: Mapping[str, Iterable[str]],
        sts_additional_constraints: Mapping[str, Mapping[str, Iterable[str]]],
    ):
        to_id = transform_name_to_id
        self._areas = {to_id(a): a for a in areas}
        self._links = {(to_id(a1), to_id(a2)): (a1, a2) for a1, a2 in links}
        self._thermals = {to_id(a): {to_id(cl): cl for cl in clusters} for a, clusters in thermals.items()}
        self._renewables = {to_id(a): {to_id(cl): cl for cl in clusters} for a, clusters in renewables.items()}
        self._storages = {
            to_id(a): {to_id(a_storage): a_storage for a_storage in a_storages} for a, a_storages in storages.items()
        }
        self._bc_groups = {to_id(g): g for g in bc_groups}
        self._sts_additional_constraints = {
            to_id(a): {to_id(s): {to_id(c) for c in s_constraints} for s, s_constraints in a_storages.items()}
            for a, a_storages in sts_additional_constraints.items()
        }

    @property
    def area_ids(self) -> Iterable[str]:
        return self._areas.keys()

    @property
    def thermal_ids(self) -> Mapping[str, Iterable[str]]:
        return self._thermals

    @property
    def renewable_ids(self) -> Mapping[str, Iterable[str]]:
        return self._renewables

    @property
    def bc_group_ids(self) -> Iterable[str]:
        return self._bc_groups

    @property
    def storage_ids(self) -> Mapping[str, Iterable[str]]:
        return self._storages

    @property
    def link_ids(self) -> Iterable[str]:
        return [f"{a1} / {a2}" for a1, a2 in self._links.keys()]

    @property
    def sts_constraint_ids(self) -> Mapping[str, Mapping[str, Iterable[str]]]:
        return self._sts_additional_constraints
