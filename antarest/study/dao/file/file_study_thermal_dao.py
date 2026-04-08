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
from abc import ABC, abstractmethod
from collections.abc import Sequence
from typing import TYPE_CHECKING, Any, Callable

import polars as pl
from typing_extensions import override

from antarest.core.exceptions import (
    AreaNotFound,
    ChildNotFoundError,
    ThermalClusterConfigNotFound,
    ThermalClusterNotFound,
)
from antarest.core.utils.utils import remove_first_match
from antarest.study.business.model.thermal_cluster_model import ThermalCluster
from antarest.study.dao.api.thermal_dao import ThermalDao
from antarest.study.dao.common import AreaId, ThermalId, ThermalSeriesMapping
from antarest.study.storage.rawstudy.model.filesystem.config.model import FileStudyTreeConfig
from antarest.study.storage.rawstudy.model.filesystem.config.thermal import (
    parse_thermal_cluster,
    serialize_thermal_cluster,
)
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.rawstudy.model.filesystem.matrix.matrix import MatrixNode

if TYPE_CHECKING:
    from antarest.study.dao.file.file_study_dao import FileStudyTreeDao

_CLUSTER_PATH = "input/thermal/clusters/{area_id}/list/{cluster_id}"
_CLUSTERS_PATH = "input/thermal/clusters/{area_id}/list"
_ALL_CLUSTERS_PATH = "input/thermal/clusters"


def _check_area_exists(study_data: FileStudyTreeConfig, area_id: str) -> None:
    if area_id not in study_data.areas:
        raise AreaNotFound(f"The area '{area_id}' does not exist")


def _get_co2_cost_matrix_path(area_id: AreaId, thermal_id: ThermalId) -> list[str]:
    return ["input", "thermal", "series", area_id, thermal_id, "CO2Cost"]


def _get_fuel_cost_matrix_path(area_id: AreaId, thermal_id: ThermalId) -> list[str]:
    return ["input", "thermal", "series", area_id, thermal_id, "fuelCost"]


def _get_series_matrix_path(area_id: AreaId, thermal_id: ThermalId) -> list[str]:
    return ["input", "thermal", "series", area_id, thermal_id, "series"]


def _get_modulation_matrix_path(area_id: AreaId, thermal_id: ThermalId) -> list[str]:
    return ["input", "thermal", "prepro", area_id, thermal_id, "modulation"]


def _get_prepro_matrix_path(area_id: AreaId, thermal_id: ThermalId) -> list[str]:
    return ["input", "thermal", "prepro", area_id, thermal_id, "data"]


class FileStudyThermalDao(ThermalDao, ABC):
    @abstractmethod
    def get_file_study(self) -> FileStudy:
        pass

    @abstractmethod
    def get_impl(self) -> "FileStudyTreeDao":
        pass

    @override
    def get_all_thermals(self) -> dict[str, dict[str, ThermalCluster]]:
        """
        Returns for each area id, a mapping of a cluster id (in lower case) towards the corresponding cluster object.
        """
        file_study = self.get_file_study()
        version = file_study.config.version
        path = _ALL_CLUSTERS_PATH
        try:
            # may raise KeyError if the path is missing
            clusters = file_study.tree.get(path.split("/"), depth=5)
            # may raise KeyError if "list" is missing
            clusters = {area_id: cluster_list["list"] for area_id, cluster_list in clusters.items()}
        except KeyError:
            raise ThermalClusterConfigNotFound(path) from None

        thermals_by_areas: dict[str, dict[str, ThermalCluster]] = {}
        for area_id, cluster_obj in clusters.items():
            for cluster_id, cluster in cluster_obj.items():
                thermal = parse_thermal_cluster(version, cluster)
                thermals_by_areas.setdefault(area_id, {})[thermal.id.lower()] = thermal
        return thermals_by_areas

    @override
    def get_all_thermals_for_area(self, area_id: str) -> Sequence[ThermalCluster]:
        file_study = self.get_file_study()
        clusters_data = self._get_all_thermals_for_area(file_study, area_id)
        return [parse_thermal_cluster(file_study.config.version, c) for c in clusters_data.values()]

    @override
    def get_thermal(self, area_id: str, thermal_id: str) -> ThermalCluster:
        file_study = self.get_file_study()
        path = _CLUSTER_PATH.format(area_id=area_id, cluster_id=thermal_id)
        try:
            cluster_data = file_study.tree.get(path.split("/"), depth=1)
        except KeyError:
            raise ThermalClusterNotFound(area_id, thermal_id) from None
        return parse_thermal_cluster(file_study.config.version, cluster_data)

    @override
    def thermal_exists(self, area_id: str, thermal_id: str) -> bool:
        file_study = self.get_file_study()
        path = _CLUSTER_PATH.format(area_id=area_id, cluster_id=thermal_id)
        try:
            file_study.tree.get(path.split("/"), depth=1)
            return True
        except (KeyError, ChildNotFoundError):
            return False

    @override
    def get_thermal_prepro(self, area_id: str, thermal_id: str) -> pl.DataFrame:
        return self.get_impl().get_matrix(_get_prepro_matrix_path(area_id, thermal_id))

    @override
    def get_thermal_modulation(self, area_id: str, thermal_id: str) -> pl.DataFrame:
        return self.get_impl().get_matrix(_get_modulation_matrix_path(area_id, thermal_id))

    @override
    def get_thermal_series(self, area_id: str, thermal_id: str) -> pl.DataFrame:
        return self.get_impl().get_matrix(_get_series_matrix_path(area_id, thermal_id))

    @override
    def get_thermal_fuel_cost(self, area_id: str, thermal_id: str) -> pl.DataFrame:
        return self.get_impl().get_matrix(_get_fuel_cost_matrix_path(area_id, thermal_id))

    @override
    def get_thermal_co2_cost(self, area_id: str, thermal_id: str) -> pl.DataFrame:
        return self.get_impl().get_matrix(_get_co2_cost_matrix_path(area_id, thermal_id))

    @override
    def get_all_thermals_co2_cost(self) -> ThermalSeriesMapping:
        return self._get_thermal_matrices(_get_co2_cost_matrix_path)

    @override
    def get_all_thermals_fuel_cost(self) -> ThermalSeriesMapping:
        return self._get_thermal_matrices(_get_fuel_cost_matrix_path)

    @override
    def get_all_thermals_series(self) -> ThermalSeriesMapping:
        return self._get_thermal_matrices(_get_series_matrix_path)

    @override
    def get_all_thermals_modulation(self) -> ThermalSeriesMapping:
        return self._get_thermal_matrices(_get_modulation_matrix_path)

    @override
    def get_all_thermals_prepro(self) -> ThermalSeriesMapping:
        return self._get_thermal_matrices(_get_prepro_matrix_path)

    @override
    def save_thermal_prepro(self, series: ThermalSeriesMapping) -> None:
        self._save_thermal_matrices(series, _get_prepro_matrix_path)

    @override
    def save_thermal_modulation(self, series: ThermalSeriesMapping) -> None:
        self._save_thermal_matrices(series, _get_modulation_matrix_path)

    @override
    def save_thermal_series(self, series: ThermalSeriesMapping) -> None:
        self._save_thermal_matrices(series, _get_series_matrix_path)

    @override
    def save_thermal_fuel_cost(self, series: ThermalSeriesMapping) -> None:
        self._save_thermal_matrices(series, _get_fuel_cost_matrix_path)

    @override
    def save_thermal_co2_cost(self, series: ThermalSeriesMapping) -> None:
        self._save_thermal_matrices(series, _get_co2_cost_matrix_path)

    @override
    def save_thermals(self, data: dict[AreaId, list[ThermalCluster]]) -> None:
        study_data = self.get_file_study()
        for area_id, thermals in data.items():
            # Ensures the area exists
            _check_area_exists(study_data.config, area_id)
            # Save the new content
            ini_content = self._get_all_thermals_for_area(study_data, area_id)
            for thermal in thermals:
                self._update_thermal_config(study_data.config, area_id, thermal)
                ini_content[thermal.id] = serialize_thermal_cluster(study_data.config.version, thermal)
            study_data.tree.save(ini_content, ["input", "thermal", "clusters", area_id, "list"])

    @override
    def delete_thermal(self, area_id: str, thermal_id: str) -> None:
        study_data = self.get_file_study()
        cluster_id = thermal_id.lower()
        paths = [
            ["input", "thermal", "clusters", area_id, "list", cluster_id],
            ["input", "thermal", "prepro", area_id, cluster_id],
            ["input", "thermal", "series", area_id, cluster_id],
        ]
        if len(study_data.config.areas[area_id].thermals) == 1:
            paths.append(["input", "thermal", "prepro", area_id])
            paths.append(["input", "thermal", "series", area_id])

        if (study_data.tree.config.path / "user" / "ts-generator-output" / "thermal" / area_id / cluster_id).exists():
            study_data.tree.delete(["user", "ts-generator-output", "thermal", area_id, cluster_id])

        for path in paths:
            study_data.tree.delete(path)

        self._remove_cluster_from_scenario_builder(study_data, area_id, cluster_id)
        # Deleting the thermal cluster in the configuration must be done AFTER deleting the files and folders.
        remove_first_match(study_data.config.areas[area_id].thermals, lambda c: c.id.lower() == cluster_id)

    def _get_thermal_matrices(self, url_getter: Callable[[AreaId, ThermalId], list[str]]) -> ThermalSeriesMapping:
        study_data = self.get_file_study()
        matrix_nodes = {}

        areas = study_data.config.areas
        for area_id, value in areas.items():
            for thermal in value.thermals:
                thermal_id = thermal.id.lower()
                url = url_getter(area_id, thermal_id)
                node = study_data.tree.get_node(url)
                assert isinstance(node, MatrixNode)
                matrix_nodes[node] = (area_id, thermal_id)

        result: ThermalSeriesMapping = {}

        matrices_mapping = self.get_impl().get_matrices_ids(list(matrix_nodes))

        for node, matrix_id in matrices_mapping.items():
            area_id, thermal_id = matrix_nodes[node]
            result.setdefault(area_id, {})[thermal_id] = matrix_id

        return result

    def _save_thermal_matrices(
        self, series: ThermalSeriesMapping, url_getter: Callable[[AreaId, ThermalId], list[str]]
    ) -> None:
        matrices_mapping: dict[str, list[MatrixNode]] = {}
        study_data = self.get_file_study()
        for area_id, value in series.items():
            for thermal_id, series_id in value.items():
                url = url_getter(area_id, thermal_id)
                node = study_data.tree.get_node(url)
                assert isinstance(node, MatrixNode)
                matrices_mapping.setdefault(series_id, []).append(node)
        self.get_impl().save_matrices(matrices_mapping)

    @staticmethod
    def _get_all_thermals_for_area(file_study: FileStudy, area_id: str) -> dict[str, Any]:
        path = _CLUSTERS_PATH.format(area_id=area_id)
        try:
            clusters_data = file_study.tree.get(path.split("/"), depth=3)
        except KeyError:
            raise ThermalClusterConfigNotFound(path, area_id) from None
        return clusters_data

    @staticmethod
    def _update_thermal_config(study_data: FileStudyTreeConfig, area_id: str, thermal: ThermalCluster) -> None:
        _check_area_exists(study_data, area_id)

        for k, existing_cluster in enumerate(study_data.areas[area_id].thermals):
            if existing_cluster.id == thermal.id:
                study_data.areas[area_id].thermals[k] = thermal
                return
        study_data.areas[area_id].thermals.append(thermal)

    @staticmethod
    def _remove_cluster_from_scenario_builder(study_data: FileStudy, area_id: str, thermal_id: str) -> None:
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
