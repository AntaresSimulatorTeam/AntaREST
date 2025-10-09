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
from typing import TYPE_CHECKING, Dict

from antarest.core.exceptions import AreaNotFound
from antarest.study.business.model.hydro_allocation_model import HydroAllocation, HydroAllocationArea
from antarest.study.business.model.hydro_correlation_model import HydroCorrelation
from antarest.study.storage.rawstudy.model.filesystem.config.identifier import transform_name_to_id

if TYPE_CHECKING:
    from antarest.study.dao.file.file_study_dao import FileStudyTreeDao

from typing_extensions import override

from antarest.study.business.model.hydro_model import HydroManagement, HydroProperties, InflowStructure
from antarest.study.dao.api.hydro_dao import HydroDao
from antarest.study.storage.rawstudy.model.filesystem.config.hydro import (
    parse_hydro_management,
    parse_inflow_structure,
    serialize_hydro_management,
    serialize_inflow_structure,
)
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy

HYDRO_PATH = ["input", "hydro", "hydro"]


def get_inflow_path(area_id: str) -> list[str]:
    return ["input", "hydro", "prepro", area_id, "prepro", "prepro"]


def get_allocation_path(area_id: str) -> list[str]:
    return ["input", "hydro", "allocation", area_id]


class FileStudyHydroDao(HydroDao):
    @abstractmethod
    def get_file_study(self) -> FileStudy:
        pass

    @abstractmethod
    def get_impl(self) -> "FileStudyTreeDao":
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
    def get_hydro_allocation(self, area_id: str) -> HydroAllocation:
        file_study = self.get_file_study()
        ini_content = file_study.tree.get(get_allocation_path(area_id))
        # allocation format can differ from the number of '[' (i.e. [[allocation]] or [allocation])
        allocation_data = ini_content.get("[allocation]", ini_content.get("allocation", {}))
        allocations = []
        for area_name, coefficient in allocation_data.items():
            # Checks the written area exists in the study
            area_id = transform_name_to_id(area_name)
            if area_id not in file_study.config.areas:
                raise AreaNotFound(area_id)
            allocations.append(HydroAllocationArea(area_id=area_id, coefficient=coefficient))
        return HydroAllocation(allocation=allocations)

    @override
    def get_hydro_allocation_matrix(self) -> dict[str, HydroAllocation]:
        file_study = self.get_file_study()
        all_areas = file_study.config.areas
        return {area_id: self.get_hydro_allocation(area_id) for area_id in sorted(all_areas)}

    @override
    def get_hydro_correlation(self, area_id: str) -> HydroCorrelation:
        return self.get_hydro_correlation_matrix()[area_id]

    @override
    def get_hydro_correlation_matrix(self) -> dict[str, HydroCorrelation]:
        raise NotImplementedError()

    @override
    def save_hydro_correlation(self, correlation: dict[str, HydroCorrelation]) -> None:
        raise NotImplementedError()

    @override
    def save_hydro_management(self, hydro_management: HydroManagement, area_id: str) -> None:
        file_study = self.get_file_study()
        initial_hydro_data = file_study.tree.get(HYDRO_PATH)
        new_hydro_data = serialize_hydro_management(hydro_management, area_id, file_study.config.version)
        final_hydro_data = {key: {**initial_hydro_data.get(key, {}), **value} for key, value in new_hydro_data.items()}
        file_study.tree.save(final_hydro_data, HYDRO_PATH)

    @override
    def save_inflow_structure(self, inflow_structure: InflowStructure, area_id: str) -> None:
        file_study = self.get_file_study()
        inflow_path = get_inflow_path(area_id)
        file_data = serialize_inflow_structure(inflow_structure)
        file_study.tree.save(file_data, inflow_path)

    @override
    def save_hydro_allocation(self, area_id: str, allocation: HydroAllocation) -> None:
        file_study = self.get_file_study()
        # Checks the given areas exist in the study
        existing_areas = file_study.config.areas
        if area_id not in existing_areas:
            raise AreaNotFound(area_id)
        data = {}
        for alloc in allocation.allocation:
            if alloc.area_id not in existing_areas:
                raise AreaNotFound(alloc.area_id)
            data[alloc.area_id] = alloc.coefficient
        # Saves the data inside the file
        url = get_allocation_path(area_id)
        file_study.tree.save({"[allocation]": data}, url)
