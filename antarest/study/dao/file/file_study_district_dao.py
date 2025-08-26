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
    parse_district,
)
from antarest.study.storage.rawstudy.model.filesystem.config.identifier import transform_name_to_id
from antarest.study.storage.rawstudy.model.filesystem.config.model import (
    DistrictSet,
)
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy

DISTRICTS_PATH = ["input", "areas", "sets"]


class FileStudyDistrictDao(DistrictDao):
    @abstractmethod
    def get_file_study(self) -> FileStudy:
        pass

    @override
    def get_districts(self) -> Sequence[District]:
        """
        Returns for each area id, a mapping of a cluster id (in lower case) towards the corresponding cluster object.
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
        Returns for each area id, a mapping of a cluster id (in lower case) towards the corresponding cluster object.
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
        study_data = self.get_file_study()
        return district_id in study_data.config.sets

    @override
    def save_district(self, district: District, district_base_filter: Optional[DistrictBaseFilter]) -> None:
        study_data = self.get_file_study()
        areas = set(district.areas or [])
        all_areas = set(study_data.config.areas)
        if invalid_areas := areas - all_areas:
            raise AreaNotFound(*invalid_areas)

        district_id = transform_name_to_id(district.name)
        item_key = self._update_district_sets_config(district_id, district, district_base_filter)
        apply_filter = district_base_filter.value if district_base_filter else DistrictBaseFilter.remove_all
        study_data.tree.save(
            {
                "caption": district.name,
                "apply-filter": apply_filter,
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

        # if district_id in study_data.config.sets:
        #     return (
        #         command_failed(message=f"District '{self.name}' already exists and could not be created"),
        #         dict(),
        #     )

        base_filter = district_base_filter or DistrictBaseFilter.remove_all
        inverted_set = base_filter == DistrictBaseFilter.add_all
        study_data.config.sets[district_id] = DistrictSet(
            name=district.name,
            areas=district.areas or [],
            output=district.output,
            inverted_set=inverted_set,
        )
        # return command_succeeded(message=district_id), {
        #     "district_id": district_id,
        #     "item_key": item_key,
        # }

        return "-" if inverted_set else "+"

    @override
    def remove_district(
        self,
        district_id: str,
    ) -> None:
        """
        Remove a district from a study.

        Args:
            district_id: district identifier

        Raises:
            DistrictNotFound: exception raised when district is not found in the study.
        """
        study_data = self.get_file_study()
        study_data.tree.delete(["input", "areas", "sets", district_id])
        del study_data.config.sets[district_id]
