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
from typing import Any, Sequence

from typing_extensions import override

from antarest.core.exceptions import AreaNotFound, DistrictConfigNotFound
from antarest.study.business.model.district_model import DistrictApplyFilter, DistrictDefinition, DistrictDTO
from antarest.study.dao.api.district_dao import DistrictDao
from antarest.study.storage.rawstudy.model.filesystem.config.district import (
    DistrictFileData,
    district_set_apply_filter,
    parse_district,
)
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy

DISTRICTS_PATH = ["input", "areas", "sets"]


class FileStudyDistrictDao(DistrictDao):
    @abstractmethod
    def get_file_study(self) -> FileStudy:
        pass

    @override
    def get_districts(self) -> Sequence[DistrictDTO]:
        """
        Returns all districts of the study.
        """
        file_study = self.get_file_study()
        path = DISTRICTS_PATH
        try:
            # may raise KeyError if the path is missing
            districts = file_study.tree.get(path)
            # may raise KeyError if "list" is missing
        except KeyError:
            raise DistrictConfigNotFound(str(path))

        all_areas = list(file_study.config.areas)
        return [
            parse_district(district_data, district_id).to_dto(all_areas)
            for district_id, district_data in districts.items()
        ]

    @override
    def get_district(self, district_id: str) -> DistrictDTO:
        """
        Get the district with the given district id.
        """
        study_data = self.get_file_study()
        path = DISTRICTS_PATH + [district_id]
        try:
            # may raise KeyError if the path is missing
            district_data = study_data.tree.get(path)
        except KeyError:
            raise DistrictConfigNotFound(str(path))

        all_areas = list(study_data.config.areas)
        return parse_district(district_data, district_id).to_dto(all_areas)

    @override
    def get_district_apply_filter(self, district_id: str) -> DistrictApplyFilter:
        """
        Returns the district base filter.
        """
        if not self.district_exists(district_id):
            raise DistrictConfigNotFound(district_id)

        study_data = self.get_file_study()
        path = DISTRICTS_PATH + [district_id]
        try:
            # may raise KeyError if the path is missing
            district_data = study_data.tree.get(path)
        except KeyError:
            raise DistrictConfigNotFound(str(path))

        return district_set_apply_filter(district_data)

    @override
    def district_exists(self, district_id: str) -> bool:
        """
        Returns whether a district with the given id exists in the study.
        """
        study_data = self.get_file_study()
        return district_id in study_data.config.sets

    @override
    def save_district(self, district: DistrictDefinition) -> None:
        """
        Save a new district to a study.

        If the district already exists, it will be overwritten.
        """
        study_data = self.get_file_study()
        invalid_areas = self.get_invalid_areas_in_district(district.add_areas + district.substract_areas)
        if invalid_areas:
            raise AreaNotFound(*invalid_areas)

        # Update the in-memory config
        study_data.config.sets[district.id] = DistrictFileData.from_model(district)

        # Persist the change in the filesystem
        district_data_tree: dict[str, Any] = {
            "caption": district.name,
            "apply-filter": district.apply_filter.value,
            "output": district.output,
            "comments": district.comments,
        }
        if district.add_areas:
            district_data_tree["+"] = district.add_areas
        if district.substract_areas:
            district_data_tree["-"] = district.substract_areas

        study_data.tree.save(
            district_data_tree,
            ["input", "areas", "sets", district.id],
        )

    @override
    def remove_district(
        self,
        district_id: str,
    ) -> None:
        """
        Remove a district from a study.
        """
        study_data = self.get_file_study()
        study_data.tree.delete(["input", "areas", "sets", district_id])
        del study_data.config.sets[district_id]

    @override
    def get_invalid_areas_in_district(self, areas: list[str]) -> list[str]:
        """
        Check all areas exists in the study.

        TODO this method should be moved to the area DAO when we'll implement it
        """
        areas_set = set(areas)
        study_data = self.get_file_study()
        all_areas = set(study_data.config.areas)
        invalid_areas = areas_set - all_areas
        return list(invalid_areas)
