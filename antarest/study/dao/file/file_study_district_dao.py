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
from typing import Literal, Optional, Sequence

from typing_extensions import override

from antarest.core.exceptions import AreaNotFound, DistrictConfigNotFound
from antarest.study.business.model.district_model import District, DistrictBaseFilter
from antarest.study.dao.api.district_dao import DistrictDao
from antarest.study.storage.rawstudy.model.filesystem.config.district import (
    DistrictSet,
    areas_sign_from_base_filter,
    parse_district,
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
        path = DISTRICTS_PATH
        try:
            # may raise KeyError if the path is missing
            districts = file_study.tree.get(path)
            # may raise KeyError if "list" is missing
        except KeyError:
            raise DistrictConfigNotFound(str(path))

        all_areas = list(file_study.config.areas)
        return [
            parse_district(district_id, district_data, all_areas) for district_id, district_data in districts.items()
        ]

    @override
    def get_district(self, district_id: str) -> District:
        """
        Returns the district with the given district id.
        """
        study_data = self.get_file_study()
        path = DISTRICTS_PATH + [district_id]
        try:
            # may raise KeyError if the path is missing
            district_data = study_data.tree.get(path)
        except KeyError:
            raise DistrictConfigNotFound(str(path))

        all_areas = list(study_data.config.areas)
        return parse_district(district_id, district_data, all_areas)

    @override
    def district_exists(self, district_id: str) -> bool:
        """
        Returns whether a district with the given id exists in the study.
        """
        study_data = self.get_file_study()
        return district_id in study_data.config.sets

    @override
    def save_district(self, district: District, district_base_filter: Optional[DistrictBaseFilter]) -> None:
        """
        Save a new district to a study.

        If the district already exists, it will be overwritten.

        Depending on the `district_base_filter`, the areas in the district will be stored under the key "+" or "-".
        """
        study_data = self.get_file_study()
        invalid_areas = self.get_invalid_areas_in_district(district.areas)
        if invalid_areas:
            raise AreaNotFound(*invalid_areas)

        district_id = transform_name_to_id(district.name)

        # Update the in-memory config
        study_data.config.sets[district_id] = DistrictSet.from_model(district, district_base_filter)

        # Persist the change in the filesystem
        item_key = areas_sign_from_base_filter(district_base_filter)
        apply_filter = district_base_filter if district_base_filter else DistrictBaseFilter.remove_all
        study_data.tree.save(
            {
                "caption": district.name,
                "apply-filter": apply_filter.value,
                item_key: district.areas,
                "output": district.output,
                "comments": district.comments,
            },
            ["input", "areas", "sets", district_id],
        )

    def _update_district_sets_config(
        self, district_id: str, district: District, district_base_filter: Optional[DistrictBaseFilter]
    ) -> Literal["+", "-"]:
        study_data = self.get_file_study()
        base_filter = district_base_filter or DistrictBaseFilter.remove_all
        inverted_set = base_filter == DistrictBaseFilter.add_all
        study_data.config.sets[district_id] = DistrictSet(
            name=district.name,
            areas=district.areas,
            output=district.output,
            inverted_set=inverted_set,
        )
        return "-" if inverted_set else "+"

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
