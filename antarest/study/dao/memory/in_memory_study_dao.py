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

import pandas as pd
from antares.study.version import StudyVersion
from typing_extensions import override

from antarest.core.exceptions import LinkNotFound
from antarest.matrixstore.service import ISimpleMatrixService
from antarest.study.business.model.binding_constraint_model import BindingConstraint
from antarest.study.business.model.link_model import Link
from antarest.study.business.model.renewable_cluster_model import RenewableCluster
from antarest.study.business.model.sts_model import STStorage, STStorageAdditionalConstraint
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


@dataclass(frozen=True)
class AdditionalConstraintKey:
    area_id: str
    constraint_id: str


def link_key(area1_id: str, area2_id: str) -> LinkKey:
    area1_id, area2_id = sorted((area1_id, area2_id))
    return LinkKey(area1_id, area2_id)


def cluster_key(area_id: str, cluster_id: str) -> ClusterKey:
    return ClusterKey(area_id, cluster_id)


def additional_constraint_key(area_id: str, constraint_id: str) -> AdditionalConstraintKey:
    return AdditionalConstraintKey(area_id, constraint_id)


class InMemoryStudyDao(StudyDao):
    """
    In memory implementation of study DAO, mainly for testing purposes.
    TODO, warning: no version handling, no check on areas, no checks on matrices ...
    """

    def __init__(self, version: StudyVersion, matrix_service: ISimpleMatrixService) -> None:
        self._version = version
        self._matrix_service = matrix_service
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
        # Renewables
        self._renewables: Dict[ClusterKey, RenewableCluster] = {}
        self._renewable_series: Dict[ClusterKey, str] = {}
        # Short-term storages
        self._st_storages: Dict[ClusterKey, STStorage] = {}
        self._storage_pmax_injection: Dict[ClusterKey, str] = {}
        self._storage_pmax_withdrawal: Dict[ClusterKey, str] = {}
        self._storage_lower_rule_curve: Dict[ClusterKey, str] = {}
        self._storage_upper_rule_curve: Dict[ClusterKey, str] = {}
        self._storage_inflows: Dict[ClusterKey, str] = {}
        self._storage_cost_injection: Dict[ClusterKey, str] = {}
        self._storage_cost_withdrawal: Dict[ClusterKey, str] = {}
        self._storage_cost_level: Dict[ClusterKey, str] = {}
        self._storage_cost_variation_injection: Dict[ClusterKey, str] = {}
        self._storage_cost_variation_withdrawal: Dict[ClusterKey, str] = {}
        # Short-term storages additional constraints
        self._st_storages_constraints: dict[str, list[STStorageAdditionalConstraint]] = {}
        self._st_storages_constraints_terms: Dict[AdditionalConstraintKey, pd.DataFrame] = {}
        # Binding constraints
        self._constraints: Dict[str, BindingConstraint] = {}
        self._constraints_values_matrix: dict[str, str] = {}
        self._constraints_less_term_matrix: dict[str, str] = {}
        self._constraints_greater_term_matrix: dict[str, str] = {}
        self._constraints_equal_term_matrix: dict[str, str] = {}

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
        return [thermal for key, thermal in self._thermals.items() if key.area_id == area_id]

    @override
    def get_thermal(self, area_id: str, thermal_id: str) -> ThermalCluster:
        return self._thermals[cluster_key(area_id, thermal_id)]

    @override
    def thermal_exists(self, area_id: str, thermal_id: str) -> bool:
        return cluster_key(area_id, thermal_id) in self._thermals

    @override
    def get_thermal_prepro(self, area_id: str, thermal_id: str) -> pd.DataFrame:
        matrix_id = self._thermal_prepro[cluster_key(area_id, thermal_id)]
        return self._matrix_service.get(matrix_id)

    @override
    def get_thermal_modulation(self, area_id: str, thermal_id: str) -> pd.DataFrame:
        matrix_id = self._thermal_modulation[cluster_key(area_id, thermal_id)]
        return self._matrix_service.get(matrix_id)

    @override
    def get_thermal_series(self, area_id: str, thermal_id: str) -> pd.DataFrame:
        matrix_id = self._thermal_series[cluster_key(area_id, thermal_id)]
        return self._matrix_service.get(matrix_id)

    @override
    def get_thermal_fuel_cost(self, area_id: str, thermal_id: str) -> pd.DataFrame:
        matrix_id = self._thermal_fuel_cost[cluster_key(area_id, thermal_id)]
        return self._matrix_service.get(matrix_id)

    @override
    def get_thermal_co2_cost(self, area_id: str, thermal_id: str) -> pd.DataFrame:
        matrix_id = self._thermal_co2_cost[cluster_key(area_id, thermal_id)]
        return self._matrix_service.get(matrix_id)

    @override
    def save_thermal(self, area_id: str, thermal: ThermalCluster) -> None:
        self._thermals[cluster_key(area_id, thermal.id)] = thermal

    @override
    def save_thermals(self, area_id: str, thermals: Sequence[ThermalCluster]) -> None:
        for thermal in thermals:
            self.save_thermal(area_id, thermal)

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

    @override
    def get_all_renewables(self) -> dict[str, dict[str, RenewableCluster]]:
        all_renewables: dict[str, dict[str, RenewableCluster]] = {}
        for key, renewable_cluster in self._renewables.items():
            all_renewables.setdefault(key.area_id, {})[key.cluster_id] = renewable_cluster
        return all_renewables

    @override
    def get_all_renewables_for_area(self, area_id: str) -> Sequence[RenewableCluster]:
        return [renewable for key, renewable in self._renewables.items() if key.area_id == area_id]

    @override
    def get_renewable(self, area_id: str, renewable_id: str) -> RenewableCluster:
        return self._renewables[cluster_key(area_id, renewable_id)]

    @override
    def renewable_exists(self, area_id: str, renewable_id: str) -> bool:
        return cluster_key(area_id, renewable_id) in self._renewables

    @override
    def get_renewable_series(self, area_id: str, renewable_id: str) -> pd.DataFrame:
        matrix_id = self._renewable_series[cluster_key(area_id, renewable_id)]
        return self._matrix_service.get(matrix_id)

    @override
    def save_renewable(self, area_id: str, renewable: RenewableCluster) -> None:
        self._renewables[cluster_key(area_id, renewable.id)] = renewable

    @override
    def save_renewables(self, area_id: str, renewables: Sequence[RenewableCluster]) -> None:
        for renewable in renewables:
            self.save_renewable(area_id, renewable)

    @override
    def save_renewable_series(self, area_id: str, renewable_id: str, series_id: str) -> None:
        self._renewable_series[cluster_key(area_id, renewable_id)] = series_id

    @override
    def delete_renewable(self, area_id: str, renewable: RenewableCluster) -> None:
        del self._renewables[cluster_key(area_id, renewable.id)]

    @override
    def get_all_constraints(self) -> dict[str, BindingConstraint]:
        return self._constraints

    @override
    def get_constraint(self, constraint_id: str) -> BindingConstraint:
        return self._constraints[constraint_id]

    @override
    def get_constraint_values_matrix(self, constraint_id: str) -> pd.DataFrame:
        matrix_id = self._constraints_values_matrix[constraint_id]
        return self._matrix_service.get(matrix_id)

    @override
    def get_constraint_less_term_matrix(self, constraint_id: str) -> pd.DataFrame:
        matrix_id = self._constraints_less_term_matrix[constraint_id]
        return self._matrix_service.get(matrix_id)

    @override
    def get_constraint_greater_term_matrix(self, constraint_id: str) -> pd.DataFrame:
        matrix_id = self._constraints_greater_term_matrix[constraint_id]
        return self._matrix_service.get(matrix_id)

    @override
    def get_constraint_equal_term_matrix(self, constraint_id: str) -> pd.DataFrame:
        matrix_id = self._constraints_equal_term_matrix[constraint_id]
        return self._matrix_service.get(matrix_id)

    @override
    def save_constraints(self, constraints: Sequence[BindingConstraint]) -> None:
        for constraint in constraints:
            self._constraints[constraint.id] = constraint

    @override
    def save_constraint_values_matrix(self, constraint_id: str, series_id: str) -> None:
        self._constraints_values_matrix[constraint_id] = series_id

    @override
    def save_constraint_less_term_matrix(self, constraint_id: str, series_id: str) -> None:
        self._constraints_less_term_matrix[constraint_id] = series_id

    @override
    def save_constraint_greater_term_matrix(self, constraint_id: str, series_id: str) -> None:
        self._constraints_greater_term_matrix[constraint_id] = series_id

    @override
    def save_constraint_equal_term_matrix(self, constraint_id: str, series_id: str) -> None:
        self._constraints_equal_term_matrix[constraint_id] = series_id

    @override
    def delete_constraints(self, constraints: list[BindingConstraint]) -> None:
        for constraint in constraints:
            del self._constraints[constraint.id]

    @override
    def get_all_st_storages(self) -> dict[str, dict[str, STStorage]]:
        all_storages: dict[str, dict[str, STStorage]] = {}
        for key, storage in self._st_storages.items():
            all_storages.setdefault(key.area_id, {})[key.cluster_id] = storage
        return all_storages

    @override
    def get_all_st_storages_for_area(self, area_id: str) -> Sequence[STStorage]:
        return [storage for key, storage in self._st_storages.items() if key.area_id == area_id]

    @override
    def get_st_storage(self, area_id: str, storage_id: str) -> STStorage:
        return self._st_storages[cluster_key(area_id, storage_id)]

    @override
    def st_storage_exists(self, area_id: str, storage_id: str) -> bool:
        return cluster_key(area_id, storage_id) in self._st_storages

    @override
    def get_st_storage_pmax_injection(self, area_id: str, storage_id: str) -> pd.DataFrame:
        matrix_id = self._storage_pmax_injection[cluster_key(area_id, storage_id)]
        return self._matrix_service.get(matrix_id)

    @override
    def get_st_storage_pmax_withdrawal(self, area_id: str, storage_id: str) -> pd.DataFrame:
        matrix_id = self._storage_pmax_withdrawal[cluster_key(area_id, storage_id)]
        return self._matrix_service.get(matrix_id)

    @override
    def get_st_storage_lower_rule_curve(self, area_id: str, storage_id: str) -> pd.DataFrame:
        matrix_id = self._storage_lower_rule_curve[cluster_key(area_id, storage_id)]
        return self._matrix_service.get(matrix_id)

    @override
    def get_st_storage_upper_rule_curve(self, area_id: str, storage_id: str) -> pd.DataFrame:
        matrix_id = self._storage_upper_rule_curve[cluster_key(area_id, storage_id)]
        return self._matrix_service.get(matrix_id)

    @override
    def get_st_storage_inflows(self, area_id: str, storage_id: str) -> pd.DataFrame:
        matrix_id = self._storage_inflows[cluster_key(area_id, storage_id)]
        return self._matrix_service.get(matrix_id)

    @override
    def get_st_storage_cost_injection(self, area_id: str, storage_id: str) -> pd.DataFrame:
        matrix_id = self._storage_cost_injection[cluster_key(area_id, storage_id)]
        return self._matrix_service.get(matrix_id)

    @override
    def get_st_storage_cost_withdrawal(self, area_id: str, storage_id: str) -> pd.DataFrame:
        matrix_id = self._storage_cost_withdrawal[cluster_key(area_id, storage_id)]
        return self._matrix_service.get(matrix_id)

    @override
    def get_st_storage_cost_level(self, area_id: str, storage_id: str) -> pd.DataFrame:
        matrix_id = self._storage_cost_level[cluster_key(area_id, storage_id)]
        return self._matrix_service.get(matrix_id)

    @override
    def get_st_storage_cost_variation_injection(self, area_id: str, storage_id: str) -> pd.DataFrame:
        matrix_id = self._storage_cost_variation_injection[cluster_key(area_id, storage_id)]
        return self._matrix_service.get(matrix_id)

    @override
    def get_st_storage_cost_variation_withdrawal(self, area_id: str, storage_id: str) -> pd.DataFrame:
        matrix_id = self._storage_cost_variation_withdrawal[cluster_key(area_id, storage_id)]
        return self._matrix_service.get(matrix_id)

    @override
    def save_st_storage(self, area_id: str, st_storage: STStorage) -> None:
        self._st_storages[cluster_key(area_id, st_storage.id)] = st_storage

    @override
    def save_st_storages(self, area_id: str, storages: Sequence[STStorage]) -> None:
        for storage in storages:
            self.save_st_storage(area_id, storage)

    @override
    def save_st_storage_pmax_injection(self, area_id: str, storage_id: str, series_id: str) -> None:
        self._storage_pmax_injection[cluster_key(area_id, storage_id)] = series_id

    @override
    def save_st_storage_pmax_withdrawal(self, area_id: str, storage_id: str, series_id: str) -> None:
        self._storage_pmax_withdrawal[cluster_key(area_id, storage_id)] = series_id

    @override
    def save_st_storage_lower_rule_curve(self, area_id: str, storage_id: str, series_id: str) -> None:
        self._storage_lower_rule_curve[cluster_key(area_id, storage_id)] = series_id

    @override
    def save_st_storage_upper_rule_curve(self, area_id: str, storage_id: str, series_id: str) -> None:
        self._storage_upper_rule_curve[cluster_key(area_id, storage_id)] = series_id

    @override
    def save_st_storage_inflows(self, area_id: str, storage_id: str, series_id: str) -> None:
        self._storage_inflows[cluster_key(area_id, storage_id)] = series_id

    @override
    def save_st_storage_cost_injection(self, area_id: str, storage_id: str, series_id: str) -> None:
        self._storage_cost_injection[cluster_key(area_id, storage_id)] = series_id

    @override
    def save_st_storage_cost_withdrawal(self, area_id: str, storage_id: str, series_id: str) -> None:
        self._storage_cost_withdrawal[cluster_key(area_id, storage_id)] = series_id

    @override
    def save_st_storage_cost_level(self, area_id: str, storage_id: str, series_id: str) -> None:
        self._storage_cost_level[cluster_key(area_id, storage_id)] = series_id

    @override
    def save_st_storage_cost_variation_injection(self, area_id: str, storage_id: str, series_id: str) -> None:
        self._storage_cost_variation_injection[cluster_key(area_id, storage_id)] = series_id

    @override
    def save_st_storage_cost_variation_withdrawal(self, area_id: str, storage_id: str, series_id: str) -> None:
        self._storage_cost_variation_withdrawal[cluster_key(area_id, storage_id)] = series_id

    @override
    def delete_storage(self, area_id: str, storage: STStorage) -> None:
        del self._st_storages[cluster_key(area_id, storage.id)]

    @override
    def st_storage_additional_constraint_exists(self, area_id: str, constraint_id: str) -> bool:
        for constraint in self._st_storages_constraints.get(area_id, []):
            if constraint.id == constraint_id:
                return True
        return False

    @override
    def get_all_st_storage_additional_constraints(self) -> dict[str, list[STStorageAdditionalConstraint]]:
        return self._st_storages_constraints

    @override
    def get_st_storage_additional_constraints_for_area(self, area_id: str) -> list[STStorageAdditionalConstraint]:
        return self._st_storages_constraints.get(area_id, [])

    @override
    def get_st_storage_additional_constraints(
        self, area_id: str, storage_id: str
    ) -> list[STStorageAdditionalConstraint]:
        return [c for c in self._st_storages_constraints.get(area_id, []) if c.cluster == storage_id]

    @override
    def get_st_storage_constraint_matrix(self, area_id: str, constraint_id: str) -> pd.DataFrame:
        return self._st_storages_constraints_terms[additional_constraint_key(area_id, constraint_id)]

    @override
    def delete_storage_additional_constraints(self, area_id: str, constraints: list[str]) -> None:
        constraints_to_remove = []
        for constraint in self._st_storages_constraints[area_id]:
            if constraint.id in constraints:
                constraints_to_remove.append(constraint)
        for constraint in constraints_to_remove:
            self._st_storages_constraints[area_id].remove(constraint)

    @override
    def save_storage_additional_constraints(
        self, area_id: str, constraints: list[STStorageAdditionalConstraint]
    ) -> None:
        existing_constraints = self._st_storages_constraints.get(area_id, [])
        existing_map = {}
        for constraint in existing_constraints:
            existing_map[constraint.id] = constraint

        for constraint in constraints:
            existing_map[constraint.id] = constraint

        self._st_storages_constraints[area_id] = list(existing_map.values())
