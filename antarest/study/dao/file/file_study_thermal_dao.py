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
    def delete_thermal(self, thermal: ThermalCluster) -> None:
        raise NotImplementedError()
