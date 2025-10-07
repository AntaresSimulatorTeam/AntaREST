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
    def get_all_areas_ui_info(self) -> Dict[str, Any]:
        """
        Retrieve information about all areas' user interface (UI) from the study.

        Returns:
            Dictionary where keys are area IDs, and values are UI objects.

        Raises:
            ChildNotFoundError: if one of the Area IDs is not found in the configuration.
        """
        file_study = self.get_file_study()
        area_ids = list(file_study.config.areas)

        # If there is no ID, return an empty dictionary
        if not area_ids:
            return {}

        # Import AreaUIFileData here to avoid circular import
        from antarest.study.storage.rawstudy.model.filesystem.config.area import AreaUIFileData

        ui_info_map = file_study.tree.get(["input", "areas", ",".join(area_ids), "ui"])

        # If there is only one ID, the result is a single UI object
        # Otherwise, it's a dictionary with IDs as keys
        if len(area_ids) == 1:
            ui_info_map = {area_ids[0]: ui_info_map}

        # Convert to AreaUIFileData to ensure that the UI object is valid
        ui_info_map = {area_id: AreaUIFileData(**ui_info).to_config() for area_id, ui_info in ui_info_map.items()}

        return ui_info_map
