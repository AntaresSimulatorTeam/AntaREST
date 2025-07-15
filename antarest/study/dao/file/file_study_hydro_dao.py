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

from antarest.study.business.model.hydro_model import (
    HydroManagement,
    HydroManagementFileData,
    HydroProperties,
    InflowStructure,
)
from antarest.study.dao.api.hydro_dao import HydroDao
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy

_INFLOW_PATH = "input/hydro/prepro/{area_id}/prepro/prepro"
_HYDRO_PATH = "input/hydro/hydro"


class FileStudyHydroDao(HydroDao):
    @abstractmethod
    def get_file_study(self) -> FileStudy:
        pass

    @override
    def get_all_hydro_properties(self) -> Dict[str, HydroProperties]:
        """
        Return all hydro properties for all areas within a study.
        """
        all_hydro_properties = {}

        study_data = self.get_file_study()
        hydro_management_file_data = HydroManagementFileData(**study_data.tree.get(_HYDRO_PATH.split("/")))

        for area_id in study_data.config.areas:
            hydro_management = hydro_management_file_data.get_hydro_management(area_id, study_data.config.version)
            inflow_structure = self.get_inflow_structure(area_id)
            hydro_properties = HydroProperties(management_options=hydro_management, inflow_structure=inflow_structure)

            all_hydro_properties[area_id] = hydro_properties

        return all_hydro_properties

    @override
    def get_hydro_for_area(self, area_id: str) -> HydroManagement:
        file_study = self.get_file_study()
        hydro_manager = HydroManagementFileData(**self.get_file_study().tree.get(_HYDRO_PATH.split("/")))
        return hydro_manager.get_hydro_management(area_id, file_study.config.version)

    @override
    def get_inflow_structure(self, area_id: str) -> InflowStructure:
        file_study = self.get_file_study()
        inter_monthly_correlation = file_study.tree.get(_INFLOW_PATH.format(area_id=area_id).split("/")).get(
            "intermonthly-correlation", 0.5
        )
        return InflowStructure(inter_monthly_correlation=inter_monthly_correlation)

    @override
    def save_hydro_management(self, hydro_data: Dict[str, Any]) -> None:
        study_data = self.get_file_study()
        study_data.tree.save(hydro_data, _HYDRO_PATH.split("/"))

    @override
    def save_inflow_structure(self, inflow_structure: Dict[str, str], path: List[str]) -> None:
        study_data = self.get_file_study()
        study_data.tree.save(inflow_structure, path)
