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
    parse_hydro_management,
    parse_inflow_structure,
    serialize_hydro_management,
    serialize_inflow_structure,
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

        file_study = self.get_file_study()
        file_data = file_study.tree.get(HYDRO_PATH)

        for area_id in file_study.config.areas:
            hydro_management = parse_hydro_management(area_id, file_data, file_study.config.version)
            inflow_structure = self.get_inflow_structure(area_id)
            hydro_properties = HydroProperties(management_options=hydro_management, inflow_structure=inflow_structure)

            all_hydro_properties[area_id] = hydro_properties

        return all_hydro_properties

    @override
    def get_hydro_management(self, area_id: str) -> HydroManagement:
        file_study = self.get_file_study()
        file_data = file_study.tree.get(HYDRO_PATH)
        return parse_hydro_management(area_id, file_data, file_study.config.version)

    @override
    def get_inflow_structure(self, area_id: str) -> InflowStructure:
        file_study = self.get_file_study()
        file_data = file_study.tree.get(get_inflow_path(area_id))
        return parse_inflow_structure(file_data)

    @override
    def save_hydro_management(self, hydro_management: HydroManagement, area_id: str) -> None:
        file_study = self.get_file_study()
        initial_hydro_data = file_study.tree.get(HYDRO_PATH)
        new_hydro_data = serialize_hydro_management(hydro_management, area_id, file_study.config.version)
        updated_hydro_data = {
            field: {**initial_hydro_data.get(field, {}), **new_hydro_data[field]} for field in new_hydro_data.keys()
        }
        file_study.tree.save(updated_hydro_data, HYDRO_PATH)

    @override
    def save_inflow_structure(self, inflow_structure: InflowStructure, area_id: str) -> None:
        file_study = self.get_file_study()
        inflow_path = get_inflow_path(area_id)
        file_data = serialize_inflow_structure(inflow_structure)
        file_study.tree.save(file_data, inflow_path)
