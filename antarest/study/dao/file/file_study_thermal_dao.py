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
from abc import ABC, abstractmethod
from typing import Sequence

from typing_extensions import override

from antarest.core.exceptions import ThermalClusterConfigNotFound, ThermalClusterNotFound
from antarest.study.business.model.thermal_cluster_model import ThermalCluster
from antarest.study.dao.api.thermal_dao import ThermalDao
from antarest.study.model import STUDY_VERSION_8_7
from antarest.study.storage.rawstudy.model.filesystem.config.model import FileStudyTreeConfig
from antarest.study.storage.rawstudy.model.filesystem.config.thermal import (
    parse_thermal_cluster,
    serialize_thermal_cluster,
)
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy

_CLUSTER_PATH = "input/thermal/clusters/{area_id}/list/{cluster_id}"
_CLUSTERS_PATH = "input/thermal/clusters/{area_id}/list"
_ALL_CLUSTERS_PATH = "input/thermal/clusters"


class FileStudyThermalDao(ThermalDao, ABC):
    @abstractmethod
    def get_file_study(self) -> FileStudy:
        pass

    @override
    def get_thermals(self, area_id: str) -> Sequence[ThermalCluster]:
        file_study = self.get_file_study()
        path = _CLUSTERS_PATH.format(area_id=area_id)
        try:
            clusters_data = file_study.tree.get(path.split("/"), depth=3)
        except KeyError:
            raise ThermalClusterConfigNotFound(path, area_id) from None
        return [parse_thermal_cluster(file_study.config.version, c) for c in clusters_data.values()]

    @override
    def get_thermal(self, area_id: str, thermal_id: str) -> ThermalCluster:
        file_study = self.get_file_study()
        path = _CLUSTER_PATH.format(area_id=area_id, cluster_id=thermal_id)
        try:
            cluster_data = file_study.tree.get(path.split("/"), depth=1)
        except KeyError:
            raise ThermalClusterNotFound(path, thermal_id) from None
        return parse_thermal_cluster(file_study.config.version, cluster_data)

    @override
    def thermal_exists(self, area_id: str, thermal_id: str) -> bool:
        file_study = self.get_file_study()
        path = _CLUSTER_PATH.format(area_id=area_id, cluster_id=thermal_id)
        try:
            file_study.tree.get(path.split("/"), depth=1)
            return True
        except KeyError:
            return False

    @override
    def save_thermal(self, area_id: str, thermal: ThermalCluster) -> None:
        study_data = self.get_file_study()
        self._update_thermal_config(area_id, thermal)

        study_data.tree.save(
            serialize_thermal_cluster(study_data.config.version, thermal),
            ["input", "thermal", "clusters", "properties", area_id, "list", thermal.id],
        )

    def _update_thermal_config(self, area_id: str, thermal: ThermalCluster) -> None:
        study_data = self.get_file_study().config
        if area_id not in study_data.areas:
            raise ValueError(f"The area '{area_id}' does not exist")

        for k, existing_cluster in enumerate(study_data.areas[area_id].thermals):
            if existing_cluster.id == thermal.id:
                study_data.areas[area_id].thermals[k] = thermal
                return
        study_data.areas[area_id].thermals.append(thermal)

    @override
    def save_thermal_prepro(self, area_id: str, thermal_id: str, series_id: str) -> None:
        study_data = self.get_file_study()
        study_data.tree.save(series_id, ["input", "thermal", "prepro", area_id, thermal_id, "data"])

    @override
    def save_thermal_modulation(self, area_id: str, thermal_id: str, series_id: str) -> None:
        study_data = self.get_file_study()
        study_data.tree.save(series_id, ["input", "thermal", "prepro", area_id, thermal_id, "modulation"])

    @override
    def save_thermal_series(self, area_id: str, thermal_id: str, series_id: str) -> None:
        study_data = self.get_file_study()
        study_data.tree.save(series_id, ["input", "thermal", "series", area_id, thermal_id, "series"])

    @override
    def save_thermal_fuel_cost(self, area_id: str, thermal_id: str, series_id: str) -> None:
        study_data = self.get_file_study()
        study_version = study_data.config.version
        if study_version < STUDY_VERSION_8_7:
            raise ValueError(f"fuelCost matrix is supported since version 8.7 and your study is in {study_version}")
        study_data.tree.save(series_id, ["input", "thermal", "series", area_id, thermal_id, "fuelCost"])

    @override
    def save_thermal_co2_cost(self, area_id: str, thermal_id: str, series_id: str) -> None:
        study_data = self.get_file_study()
        study_version = study_data.config.version
        if study_version < STUDY_VERSION_8_7:
            raise ValueError(f"C02Cost matrix is supported since version 8.7 and your study is in {study_version}")
        study_data.tree.save(series_id, ["input", "thermal", "series", area_id, thermal_id, "fuelCost"])

    @override
    def delete_thermal(self, area_id: str, thermal: ThermalCluster) -> None:
        study_data = self.get_file_study()

        paths = [
            ["input", "thermal", "clusters", area_id, "list", thermal.id],
            ["input", "thermal", "prepro", area_id, thermal.id],
            ["input", "thermal", "series", area_id, thermal.id],
        ]
        if len(study_data.config.areas[area_id].thermals) == 1:
            paths.append(["input", "thermal", "prepro", area_id])
            paths.append(["input", "thermal", "series", area_id])

        for path in paths:
            study_data.tree.delete(path)

        self._remove_cluster_from_binding_constraints(study_data, area_id, thermal.id)
        self._remove_cluster_from_scenario_builder(study_data, area_id, thermal.id)
        # Deleting the thermal cluster in the configuration must be done AFTER deleting the files and folders.
        return self._remove_from_config(study_data.config, area_id, thermal)

    def _remove_cluster_from_scenario_builder(self, study_data: FileStudy, area_id: str, thermal_id: str) -> None:
        """
        Update the scenario builder by removing the rows that correspond to the thermal cluster to remove.

        NOTE: this update can be very long if the scenario builder configuration is large.
        """
        rulesets = study_data.tree.get(["settings", "scenariobuilder"])

        for ruleset in rulesets.values():
            for key in list(ruleset):
                # The key is in the form "symbol,area,year,cluster"
                symbol, *parts = key.split(",")
                if symbol == "t" and parts[0] == area_id and parts[2] == thermal_id:
                    del ruleset[key]

        study_data.tree.save(rulesets, ["settings", "scenariobuilder"])

    def _remove_cluster_from_binding_constraints(self, study_data: FileStudy, area_id: str, thermal_id: str) -> None:
        """
        Remove the binding constraints that are related to the thermal cluster.

        Notes:
            A binding constraint has properties, a list of terms (which form a linear equation) and
            a right-hand side (which is the matrix of the binding constraint).
            The terms are of the form `area1%area2` or `area.cluster` where `area` is the ID of the area
            and `cluster` is the ID of the cluster.

            When a thermal cluster is removed, it has an impact on the terms of the binding constraints.
            At first, we could decide to remove the terms that are related to the area.
            However, this would lead to a linear equation that is not valid anymore.

            Instead, we decide to remove the binding constraints that are related to the cluster.
        """
        # See also `RemoveCluster`
        # noinspection SpellCheckingInspection
        url = ["input", "bindingconstraints", "bindingconstraints"]
        binding_constraints = study_data.tree.get(url)

        # Collect the binding constraints that are related to the area to remove
        # by searching the terms that contain the ID of the area.
        bc_to_remove = []
        for bc_index, bc in list(binding_constraints.items()):
            for key in bc:
                if "." not in key:
                    # This key identifies a link or belongs to the set of properties.
                    # It isn't a cluster ID, so we skip it.
                    continue
                # Term IDs are in the form `area1%area2` or `area.cluster`
                # noinspection PyTypeChecker
                related_area_id, related_cluster_id = map(str.lower, key.split("."))
                if (area_id, thermal_id) == (related_area_id, related_cluster_id):
                    bc_to_remove.append(binding_constraints.pop(bc_index)["id"])
                    break

        matrix_suffixes = ["_lt", "_gt", "_eq"] if study_data.config.version >= 870 else [""]

        existing_files = study_data.tree.get(["input", "bindingconstraints"], depth=1)
        for bc_id, suffix in zip(bc_to_remove, matrix_suffixes):
            matrix_id = f"{bc_id}{suffix}"
            if matrix_id in existing_files:
                study_data.tree.delete(["input", "bindingconstraints", matrix_id])

        study_data.tree.save(binding_constraints, url)

    def _remove_from_config(self, study_data: FileStudyTreeConfig, area_id: str, thermal: ThermalCluster) -> None:
        study_data.areas[area_id].thermals.remove(thermal)

        # Also removes thermal cluster from constraint terms
        # Cluster IDs are stored in lower case in the binding constraints file.
        selection = [b for b in study_data.bindings if f"{area_id}.{thermal.id}" in b.clusters]
        for binding in selection:
            study_data.bindings.remove(binding)
