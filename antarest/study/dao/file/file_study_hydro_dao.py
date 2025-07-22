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
from typing import Dict

from typing_extensions import override

from antarest.study.business.model.hydro_model import (
    HYDRO_PATH,
    HydroManagement,
    HydroProperties,
    InflowStructure,
    get_inflow_path,
)
from antarest.study.dao.api.hydro_dao import HydroDao
from antarest.study.storage.rawstudy.model.filesystem.config.hydro import (
    HydroManagementFileData,
    InflowStructureFileData,
)
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy


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
        hydro_management_file_data = HydroManagementFileData(**study_data.tree.get(HYDRO_PATH))

        for area_id in study_data.config.areas:
            hydro_management = hydro_management_file_data.get_hydro_management(area_id, study_data.config.version)
            inflow_structure = self.get_inflow_structure(area_id)
            hydro_properties = HydroProperties(management_options=hydro_management, inflow_structure=inflow_structure)

            all_hydro_properties[area_id] = hydro_properties

        return all_hydro_properties

    @override
    def get_hydro_management(self, area_id: str) -> HydroManagement:
        file_study = self.get_file_study()
        hydro_manager = HydroManagementFileData(**self.get_file_study().tree.get(HYDRO_PATH))
        return hydro_manager.get_hydro_management(area_id, file_study.config.version)

    @override
    def get_inflow_structure(self, area_id: str) -> InflowStructure:
        file_study = self.get_file_study()
        inflow_path = get_inflow_path(area_id)
        inter_monthly_correlation = file_study.tree.get(inflow_path).get("intermonthly-correlation")
        return InflowStructure(inter_monthly_correlation=inter_monthly_correlation)

    @override
    def save_hydro_management(self, area_id: str, hydro_data: HydroManagementFileData) -> None:
        study_data = self.get_file_study()
        study_data.tree.save(hydro_data.model_dump(by_alias=True, exclude_none=True), HYDRO_PATH)

    @override
    def save_inflow_structure(self, area_id: str, inflow_data: InflowStructureFileData) -> None:
        study_data = self.get_file_study()
        inflow_path = get_inflow_path(area_id)
        study_data.tree.save(inflow_data.model_dump(by_alias=True), inflow_path)
