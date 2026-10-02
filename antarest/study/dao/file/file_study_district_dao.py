# Copyright (c) 2026, RTE (https://www.rte-france.com)
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
from collections.abc import Sequence
from typing import TYPE_CHECKING

from typing_extensions import override

from antarest.core.exceptions import AreaNotFound, DistrictConfigNotFound
from antarest.study.business.model.district_model import District
from antarest.study.dao.api.district_dao import DistrictDao

if TYPE_CHECKING:
    from antarest.study.dao.file.file_study_dao import FileStudyTreeDao
from antarest.study.storage.rawstudy.model.filesystem.config.district import (
    parse_district,
    serialize_district,
)
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy

DISTRICTS_PATH = ["input", "areas", "sets"]


class FileStudyDistrictDao(DistrictDao):
    @abstractmethod
    def get_file_study(self) -> FileStudy:
        pass

    @abstractmethod
    def get_impl(self) -> "FileStudyTreeDao":
        pass

    @override
    def get_districts(self) -> Sequence[District]:
        """
        Returns the list of Data Transfer Objects (DTO) representing districts.
        """
        file_study = self.get_file_study()
        path = DISTRICTS_PATH
        try:
            # may raise KeyError if the path is missing
            districts = file_study.tree.get(path)
            # may raise KeyError if "list" is missing
        except KeyError:
            raise DistrictConfigNotFound(str(path))

        return [parse_district(district_data, district_id) for district_id, district_data in districts.items()]

    @override
    def get_district(self, district_id: str) -> District:
        """
        Get the Data Transfer Objects (DTO) representing the district with the given id.
        """
        study_data = self.get_file_study()
        path = DISTRICTS_PATH + [district_id]
        try:
            # may raise KeyError if the path is missing
            district_data = study_data.tree.get(path)
        except KeyError:
            raise DistrictConfigNotFound(str(path))
        return parse_district(district_data, district_id)

    @override
    def district_exists(self, district_id: str) -> bool:
        """
        Returns whether a district with the given id exists in the study.
        """
        study_data = self.get_file_study()
        path = DISTRICTS_PATH + [district_id]
        try:
            # may raise KeyError if the path is missing
            study_data.tree.get(path)
        except KeyError:
            return False
        return True

    @override
    def save_district(self, district: District) -> None:
        """
        Save a new district to a study.

        If the district already exists, it will be overwritten.
        """
        study_data = self.get_file_study()
        invalid_areas = self.get_impl().get_invalid_area_ids(district.add_areas + district.subtract_areas)
        if invalid_areas:
            raise AreaNotFound(*invalid_areas)

        # Update the in-memory config
        study_data.config.districts[district.id] = district

        # Persist the change in the filesystem
        study_data.tree.save(
            serialize_district(district),
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
        del study_data.config.districts[district_id]
