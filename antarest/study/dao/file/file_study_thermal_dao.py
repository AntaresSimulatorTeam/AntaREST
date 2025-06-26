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
from typing import Any, Sequence

import pandas as pd
from typing_extensions import override

from antarest.core.exceptions import ChildNotFoundError, ThermalClusterConfigNotFound, ThermalClusterNotFound
from antarest.study.business.model.thermal_cluster_model import ThermalCluster
from antarest.study.dao.api.thermal_dao import ThermalDao
from antarest.study.storage.rawstudy.model.filesystem.config.model import FileStudyTreeConfig
from antarest.study.storage.rawstudy.model.filesystem.config.thermal import (
    parse_thermal_cluster,
    serialize_thermal_cluster,
)
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.rawstudy.model.filesystem.matrix.input_series_matrix import InputSeriesMatrix

_CLUSTER_PATH = "input/thermal/clusters/{area_id}/list/{cluster_id}"
_CLUSTERS_PATH = "input/thermal/clusters/{area_id}/list"
_ALL_CLUSTERS_PATH = "input/thermal/clusters"


class FileStudyThermalDao(ThermalDao, ABC):
    @abstractmethod
    def get_file_study(self) -> FileStudy:
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
            raise ThermalClusterNotFound(path, thermal_id) from None
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
    def get_thermal_prepro(self, area_id: str, thermal_id: str) -> pd.DataFrame:
        study_data = self.get_file_study()
        node = study_data.tree.get_node(["input", "thermal", "prepro", area_id, thermal_id, "data"])
        assert isinstance(node, InputSeriesMatrix)
        return node.parse_as_dataframe()

    @override
    def get_thermal_modulation(self, area_id: str, thermal_id: str) -> pd.DataFrame:
        study_data = self.get_file_study()
        node = study_data.tree.get_node(["input", "thermal", "prepro", area_id, thermal_id, "modulation"])
        assert isinstance(node, InputSeriesMatrix)
        return node.parse_as_dataframe()

    @override
    def get_thermal_series(self, area_id: str, thermal_id: str) -> pd.DataFrame:
        study_data = self.get_file_study()
        node = study_data.tree.get_node(["input", "thermal", "series", area_id, thermal_id, "series"])
        assert isinstance(node, InputSeriesMatrix)
        return node.parse_as_dataframe()

    @override
    def get_thermal_fuel_cost(self, area_id: str, thermal_id: str) -> pd.DataFrame:
        study_data = self.get_file_study()
        node = study_data.tree.get_node(["input", "thermal", "series", area_id, thermal_id, "fuelCost"])
        assert isinstance(node, InputSeriesMatrix)
        return node.parse_as_dataframe()

    @override
    def get_thermal_co2_cost(self, area_id: str, thermal_id: str) -> pd.DataFrame:
        study_data = self.get_file_study()
        node = study_data.tree.get_node(["input", "thermal", "series", area_id, thermal_id, "CO2Cost"])
        assert isinstance(node, InputSeriesMatrix)
        return node.parse_as_dataframe()

    @override
    def save_thermal(self, area_id: str, thermal: ThermalCluster) -> None:
        study_data = self.get_file_study()
        self._update_thermal_config(study_data.config, area_id, thermal)

        study_data.tree.save(
            serialize_thermal_cluster(study_data.config.version, thermal),
            ["input", "thermal", "clusters", area_id, "list", thermal.id],
        )

    @override
    def save_thermals(self, area_id: str, thermals: Sequence[ThermalCluster]) -> None:
        study_data = self.get_file_study()
        ini_content = self._get_all_thermals_for_area(study_data, area_id)
        for thermal in thermals:
            self._update_thermal_config(study_data.config, area_id, thermal)
            ini_content[thermal.id] = serialize_thermal_cluster(study_data.config.version, thermal)
        study_data.tree.save(ini_content, ["input", "thermal", "clusters", area_id, "list"])

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
        study_data.tree.save(series_id, ["input", "thermal", "series", area_id, thermal_id, "fuelCost"])

    @override
    def save_thermal_co2_cost(self, area_id: str, thermal_id: str, series_id: str) -> None:
        study_data = self.get_file_study()
        study_data.tree.save(series_id, ["input", "thermal", "series", area_id, thermal_id, "CO2Cost"])

    @override
    def delete_thermal(self, area_id: str, thermal: ThermalCluster) -> None:
        study_data = self.get_file_study()
        cluster_id = thermal.id.lower()
        paths = [
            ["input", "thermal", "clusters", area_id, "list", cluster_id],
            ["input", "thermal", "prepro", area_id, cluster_id],
            ["input", "thermal", "series", area_id, cluster_id],
        ]
        if len(study_data.config.areas[area_id].thermals) == 1:
            paths.append(["input", "thermal", "prepro", area_id])
            paths.append(["input", "thermal", "series", area_id])

        for path in paths:
            study_data.tree.delete(path)

        self._remove_cluster_from_scenario_builder(study_data, area_id, cluster_id)
        # Deleting the thermal cluster in the configuration must be done AFTER deleting the files and folders.
        study_data.config.areas[area_id].thermals.remove(thermal)

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
        if area_id not in study_data.areas:
            raise ValueError(f"The area '{area_id}' does not exist")

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
