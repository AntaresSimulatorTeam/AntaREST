# Copyright (c) 2025, RTE (https://www.rte-france.com)
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

from dataclasses import dataclass
from typing import Dict, Sequence

from antares.study.version import StudyVersion
from typing_extensions import override

from antarest.core.exceptions import LinkNotFound
from antarest.study.business.model.link_model import Link
from antarest.study.business.model.thermal_cluster_model import ThermalCluster
from antarest.study.dao.api.study_dao import StudyDao
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy


@dataclass(frozen=True)
class LinkKey:
    area1_id: str
    area2_id: str


@dataclass(frozen=True)
class ClusterKey:
    area_id: str
    cluster_id: str


def link_key(area1_id: str, area2_id: str) -> LinkKey:
    area1_id, area2_id = sorted((area1_id, area2_id))
    return LinkKey(area1_id, area2_id)


def cluster_key(area_id: str, cluster_id: str) -> ClusterKey:
    return ClusterKey(area_id, cluster_id)


class InMemoryStudyDao(StudyDao):
    """
    In memory implementation of study DAO, mainly for testing purposes.
    TODO, warning: no version handling, no check on areas, no checks on matrices ...
    """

    def __init__(self, version: StudyVersion) -> None:
        self._version = version
        # Links
        self._links: Dict[LinkKey, Link] = {}
        self._link_capacities: Dict[LinkKey, str] = {}
        self._link_direct_capacities: Dict[LinkKey, str] = {}
        self._link_indirect_capacities: Dict[LinkKey, str] = {}
        # Thermals
        self._thermals: Dict[ClusterKey, ThermalCluster] = {}
        self._thermal_prepro: Dict[ClusterKey, str] = {}
        self._thermal_modulation: Dict[ClusterKey, str] = {}
        self._thermal_series: Dict[ClusterKey, str] = {}
        self._thermal_fuel_cost: Dict[ClusterKey, str] = {}
        self._thermal_co2_cost: Dict[ClusterKey, str] = {}

    @override
    def get_file_study(self) -> FileStudy:
        """
        To ease transition, to be removed when all goes through other methods
        """
        raise NotImplementedError()

    @override
    def get_version(self) -> StudyVersion:
        return self._version

    @override
    def get_links(self) -> Sequence[Link]:
        return list(self._links.values())

    @override
    def link_exists(self, area1_id: str, area2_id: str) -> bool:
        return link_key(area1_id, area2_id) in self._links

    @override
    def get_link(self, area1_id: str, area2_id: str) -> Link:
        try:
            return self._links[link_key(area1_id, area2_id)]
        except KeyError:
            raise LinkNotFound(f"The link {area1_id} -> {area2_id} is not present in the study")

    @override
    def save_link(self, link: Link) -> None:
        self._links[link_key(link.area1, link.area2)] = link

    @override
    def save_link_series(self, area_from: str, area_to: str, series_id: str) -> None:
        self._link_capacities[link_key(area_from, area_to)] = series_id

    @override
    def save_link_direct_capacities(self, area_from: str, area_to: str, series_id: str) -> None:
        self._link_direct_capacities[link_key(area_from, area_to)] = series_id

    @override
    def save_link_indirect_capacities(self, area_from: str, area_to: str, series_id: str) -> None:
        self._link_indirect_capacities[link_key(area_from, area_to)] = series_id

    @override
    def delete_link(self, link: Link) -> None:
        del self._links[link_key(link.area1, link.area2)]

    @override
    def get_all_thermals(self) -> dict[str, dict[str, ThermalCluster]]:
        all_thermals: dict[str, dict[str, ThermalCluster]] = {}
        for key, thermal_cluster in self._thermals.items():
            all_thermals.setdefault(key.area_id, {})[key.cluster_id] = thermal_cluster
        return all_thermals

    @override
    def get_all_thermals_for_area(self, area_id: str) -> Sequence[ThermalCluster]:
        return list(self._thermals.values())

    @override
    def get_thermal(self, area_id: str, thermal_id: str) -> ThermalCluster:
        return self._thermals[cluster_key(area_id, thermal_id)]

    @override
    def thermal_exists(self, area_id: str, thermal_id: str) -> bool:
        return cluster_key(area_id, thermal_id) in self._thermals

    @override
    def save_thermal(self, area_id: str, thermal: ThermalCluster) -> None:
        self._thermals[cluster_key(area_id, thermal.id)] = thermal

    @override
    def save_thermal_prepro(self, area_id: str, thermal_id: str, series_id: str) -> None:
        self._thermal_prepro[cluster_key(area_id, thermal_id)] = series_id

    @override
    def save_thermal_modulation(self, area_id: str, thermal_id: str, series_id: str) -> None:
        self._thermal_modulation[cluster_key(area_id, thermal_id)] = series_id

    @override
    def save_thermal_series(self, area_id: str, thermal_id: str, series_id: str) -> None:
        self._thermal_series[cluster_key(area_id, thermal_id)] = series_id

    @override
    def save_thermal_fuel_cost(self, area_id: str, thermal_id: str, series_id: str) -> None:
        self._thermal_fuel_cost[cluster_key(area_id, thermal_id)] = series_id

    @override
    def save_thermal_co2_cost(self, area_id: str, thermal_id: str, series_id: str) -> None:
        self._thermal_co2_cost[cluster_key(area_id, thermal_id)] = series_id

    @override
    def delete_thermal(self, area_id: str, thermal: ThermalCluster) -> None:
        del self._thermals[cluster_key(area_id, thermal.id)]
