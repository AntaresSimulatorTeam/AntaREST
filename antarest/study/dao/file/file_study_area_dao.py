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
from abc import abstractmethod
from typing import Any, Dict, List

from typing_extensions import override

from antarest.study.business.model.area_model import Area
from antarest.study.business.model.thermal_cluster_model import ThermalCluster
from antarest.study.dao.api.area_dao import AreaDao
from antarest.study.storage.rawstudy.model.filesystem.config.model import AreaConfig
from antarest.study.storage.rawstudy.model.filesystem.config.thermal import parse_thermal_cluster
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy


class FileStudyAreaDao(AreaDao):
    @abstractmethod
    def get_file_study(self) -> FileStudy:
        pass

    def _get_thermal_clusters(self, area_id: str) -> List[ThermalCluster]:
        """
        Retrieve thermal clusters for a specific area.

        Args:
            area_id: The area identifier.

        Returns:
            The list of thermal clusters for the area.
        """
        file_study = self.get_file_study()
        thermal_clusters_data = file_study.tree.get(["input", "thermal", "clusters", area_id, "list"])
        result = []
        for tid, obj in thermal_clusters_data.items():
            cluster_info = parse_thermal_cluster(file_study.config.version, obj)
            result.append(cluster_info)
        return result

    @override
    def get_all_areas(self) -> List[Area]:
        """
        Retrieve all physical areas of a study.
        """
        file_study = self.get_file_study()
        cfg_areas: Dict[str, AreaConfig] = file_study.config.areas
        return [
            Area(
                id=area_id,
                name=area.name,
                thermals=self._get_thermal_clusters(area_id),
            )
            for area_id, area in cfg_areas.items()
        ]

    @override
    def get_area(self, area_id: str) -> Area:
        """
        Retrieve a specific area by its ID.
        """
        raise NotImplementedError()

    @override
    def area_exists(self, area_id: str) -> bool:
        """
        Check if an area exists in the study.
        """
        raise NotImplementedError()

    @override
    def get_all_areas_ui_info(self) -> Dict[str, Any]:
        """
        Retrieve information about all areas' user interface (UI) from the study.
        """
        raise NotImplementedError()
