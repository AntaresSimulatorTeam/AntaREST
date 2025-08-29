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
from typing import Optional, Sequence

from typing_extensions import override

from antarest.core.exceptions import AreaNotFound, DistrictConfigNotFound
from antarest.study.business.model.district_model import District, DistrictBaseFilter
from antarest.study.dao.api.district_dao import DistrictDao
from antarest.study.storage.rawstudy.model.filesystem.config.district import (
    DistrictSet,
    areas_sign_from_base_filter,
)
from antarest.study.storage.rawstudy.model.filesystem.config.identifier import transform_name_to_id
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy

DISTRICTS_PATH = ["input", "areas", "sets"]


class FileStudyDistrictDao(DistrictDao):
    @abstractmethod
    def get_file_study(self) -> FileStudy:
        pass

    @override
    def get_districts(self) -> Sequence[District]:
        """
        Returns all districts of the study.
        """
        file_study = self.get_file_study()
        all_areas = list(file_study.config.areas)
        return [
            district_set.to_model(district_id, all_areas)
            for district_id, district_set in file_study.config.sets.items()
        ]

    @override
    def get_district(self, district_id: str) -> District:
        """
        Returns the district with the given district id.
        """
        file_study = self.get_file_study()
        all_areas = list(file_study.config.areas)
        try:
            return file_study.config.sets[district_id].to_model(district_id, all_areas)
        except KeyError:
            raise DistrictConfigNotFound(district_id)

    @override
    def district_exists(self, district_id: str) -> bool:
        """
        Returns whether a district with the given id exists in the study.
        """
        file_study = self.get_file_study()
        return district_id in file_study.config.sets

    @override
    def save_district(self, district: District, district_base_filter: Optional[DistrictBaseFilter]) -> None:
        """
        Save a new district to a study.

        If the district already exists, it will be overwritten.

        Depending on the `district_base_filter`, the areas in the district will be stored under the key "+" or "-".
        """
        file_study = self.get_file_study()
        invalid_areas = self.get_invalid_areas(district.areas)
        if invalid_areas:
            raise AreaNotFound(*invalid_areas)

        district_id = transform_name_to_id(district.name)
        all_areas = list(file_study.config.areas)
        district_set = DistrictSet.from_model(district, district_base_filter, all_areas)
        item_key = areas_sign_from_base_filter(district_base_filter)
        apply_filter = district_base_filter.value if district_base_filter else DistrictBaseFilter.remove_all
        file_study.config.sets[district_id] = district_set
        file_study.tree.save(
            {
                "caption": district_set.name,
                "apply-filter": apply_filter,
                item_key: district_set.areas,
                "output": district_set.output,
                "comments": district_set.comments,
            },
            ["input", "areas", "sets", district_id],
        )

    @override
    def remove_district(
        self,
        district_id: str,
    ) -> None:
        """
        Remove a district from a study.
        """
        file_study = self.get_file_study()
        file_study.tree.delete(["input", "areas", "sets", district_id])
        del file_study.config.sets[district_id]

    @override
    def get_invalid_areas(self, areas: list[str]) -> list[str]:
        """
        Check all areas exists in the study.

        TODO this method should be moved to the area DAO when we'll implement it
        """
        areas_set = set(areas)
        study_data = self.get_file_study()
        all_areas = set(study_data.config.areas)
        invalid_areas = areas_set - all_areas
        return list(invalid_areas)
