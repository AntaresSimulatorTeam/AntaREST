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
from antarest.study.storage.rawstudy.model.filesystem.config.thermal import parse_thermal_cluster
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
    def save_thermal(self, thermal: ThermalCluster) -> None:
        raise NotImplementedError()

    @override
    def save_thermal_prepro(self, area_id: str, thermal_id: str, series_id: str) -> None:
        raise NotImplementedError()

    @override
    def save_thermal_modulation(self, area_id: str, thermal_id: str, series_id: str) -> None:
        raise NotImplementedError()

    @override
    def save_thermal_series(self, area_id: str, thermal_id: str, series_id: str) -> None:
        raise NotImplementedError()

    @override
    def delete_thermal(self, thermal: ThermalCluster) -> None:
        raise NotImplementedError()
