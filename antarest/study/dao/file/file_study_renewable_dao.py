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

from antarest.core.exceptions import ChildNotFoundError, RenewableClusterConfigNotFound, RenewableClusterNotFound
from antarest.study.business.model.renewable_cluster_model import RenewableCluster
from antarest.study.dao.api.renewable_dao import RenewableDao
from antarest.study.storage.rawstudy.model.filesystem.config.model import FileStudyTreeConfig
from antarest.study.storage.rawstudy.model.filesystem.config.renewable import (
    parse_renewable_cluster,
    serialize_renewable_cluster,
)
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.rawstudy.model.filesystem.matrix.input_series_matrix import InputSeriesMatrix

_CLUSTER_PATH = "input/renewables/clusters/{area_id}/list/{cluster_id}"
_CLUSTERS_PATH = "input/renewables/clusters/{area_id}/list"
_ALL_CLUSTERS_PATH = "input/renewables/clusters"


class FileStudyRenewableDao(RenewableDao, ABC):
    @abstractmethod
    def get_file_study(self) -> FileStudy:
        pass

    @override
    def get_all_renewables(self) -> dict[str, dict[str, RenewableCluster]]:
        file_study = self.get_file_study()
        path = _ALL_CLUSTERS_PATH
        try:
            # may raise KeyError if the path is missing
            clusters = file_study.tree.get(path.split("/"), depth=5)
            # may raise KeyError if "list" is missing
            clusters = {area_id: cluster_list["list"] for area_id, cluster_list in clusters.items()}
        except KeyError:
            raise RenewableClusterConfigNotFound(path)

        renewables_by_areas: dict[str, dict[str, RenewableCluster]] = {}
        for area_id, cluster_obj in clusters.items():
            for cluster_id, cluster in cluster_obj.items():
                lowered_id = cluster_id.lower()
                renewables_by_areas.setdefault(area_id, {})[lowered_id] = parse_renewable_cluster(cluster)

        return renewables_by_areas

    @override
    def get_all_renewables_for_area(self, area_id: str) -> Sequence[RenewableCluster]:
        file_study = self.get_file_study()
        clusters_data = self._get_all_renewables_for_area(file_study, area_id)
        return [parse_renewable_cluster(cluster) for cluster in clusters_data.values()]

    @override
    def get_renewable(self, area_id: str, renewable_id: str) -> RenewableCluster:
        file_study = self.get_file_study()
        path = _CLUSTER_PATH.format(area_id=area_id, cluster_id=renewable_id)
        try:
            cluster = file_study.tree.get(path.split("/"), depth=1)
        except KeyError:
            raise RenewableClusterNotFound(path, renewable_id)
        return parse_renewable_cluster(cluster)

    @override
    def renewable_exists(self, area_id: str, renewable_id: str) -> bool:
        file_study = self.get_file_study()
        path = _CLUSTER_PATH.format(area_id=area_id, cluster_id=renewable_id)
        try:
            file_study.tree.get(path.split("/"), depth=1)
            return True
        except (KeyError, ChildNotFoundError):
            return False

    @override
    def get_renewable_series(self, area_id: str, renewable_id: str) -> pd.DataFrame:
        study_data = self.get_file_study()
        node = study_data.tree.get_node(["input", "renewables", "series", area_id, renewable_id, "series"])
        assert isinstance(node, InputSeriesMatrix)
        return node.parse_as_dataframe()

    @override
    def save_renewable(self, area_id: str, renewable: RenewableCluster) -> None:
        study_data = self.get_file_study()
        self._update_renewable_config(study_data.config, area_id, renewable)

        study_data.tree.save(
            serialize_renewable_cluster(renewable),
            ["input", "renewables", "clusters", area_id, "list", renewable.get_id()],
        )

    @override
    def save_renewables(self, area_id: str, renewables: Sequence[RenewableCluster]) -> None:
        study_data = self.get_file_study()
        ini_content = self._get_all_renewables_for_area(study_data, area_id)
        for renewable in renewables:
            self._update_renewable_config(study_data.config, area_id, renewable)
            ini_content[renewable.get_id()] = serialize_renewable_cluster(renewable)
        study_data.tree.save(ini_content, ["input", "thermal", "clusters", area_id, "list"])

    @override
    def save_renewable_series(self, area_id: str, renewable_id: str, series_id: str) -> None:
        study_data = self.get_file_study()
        study_data.tree.save(series_id, ["input", "renewables", "series", area_id, renewable_id, "series"])

    @override
    def delete_renewable(self, area_id: str, renewable: RenewableCluster) -> None:
        study_data = self.get_file_study()
        cluster_id = renewable.get_id().lower()
        paths = [
            ["input", "renewables", "clusters", area_id, "list", cluster_id],
            ["input", "renewables", "series", area_id, cluster_id],
        ]
        if len(study_data.config.areas[area_id].renewables) == 1:
            paths.append(["input", "renewables", "series", area_id])

        for path in paths:
            study_data.tree.delete(path)

        self._remove_cluster_from_scenario_builder(study_data, area_id, cluster_id)
        # Deleting the thermal cluster in the configuration must be done AFTER deleting the files and folders.
        study_data.config.areas[area_id].renewables.remove(renewable)

    @staticmethod
    def _get_all_renewables_for_area(file_study: FileStudy, area_id: str) -> dict[str, Any]:
        path = _CLUSTERS_PATH.format(area_id=area_id)
        try:
            clusters_data = file_study.tree.get(path.split("/"), depth=3)
        except KeyError:
            raise RenewableClusterConfigNotFound(path, area_id) from None
        return clusters_data

    @staticmethod
    def _update_renewable_config(study_data: FileStudyTreeConfig, area_id: str, renewable: RenewableCluster) -> None:
        if area_id not in study_data.areas:
            raise ValueError(f"The area '{area_id}' does not exist")

        renewable_id = renewable.get_id()
        for k, existing_cluster in enumerate(study_data.areas[area_id].renewables):
            if existing_cluster.get_id() == renewable_id:
                study_data.areas[area_id].renewables[k] = renewable
                return
        study_data.areas[area_id].renewables.append(renewable)

    @staticmethod
    def _remove_cluster_from_scenario_builder(study_data: FileStudy, area_id: str, renewable_id: str) -> None:
        """
        Update the scenario builder by removing the rows that correspond to the renewable cluster to remove.

        NOTE: this update can be very long if the scenario builder configuration is large.
        """
        rulesets = study_data.tree.get(["settings", "scenariobuilder"])

        for ruleset in rulesets.values():
            for key in list(ruleset):
                # The key is in the form "symbol,area,year,cluster"
                symbol, *parts = key.split(",")
                if symbol == "r" and parts[0] == area_id and parts[2] == renewable_id:
                    del ruleset[key]

        study_data.tree.save(rulesets, ["settings", "scenariobuilder"])
