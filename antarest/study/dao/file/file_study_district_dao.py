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

from abc import ABC, abstractmethod
from typing import List

from typing_extensions import override

from antarest.core.exceptions import DistrictNotFound
from antarest.study.business.model.district_model import District
from antarest.study.dao.api.district_dao import DistrictDao
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy


class FileStudyDistrictDao(DistrictDao, ABC):
    @abstractmethod
    def get_file_study(self) -> FileStudy:
        pass

    @override
    def get_districts(self) -> List[District]:
        file_study = self.get_file_study()
        all_areas = list(file_study.config.areas)
        districts = []
        for district_id, district in file_study.config.sets.items():
            assert district.name is not None
            comments = file_study.tree.get(["input", "areas", "sets", district_id]).get("comments", "")
            districts.append(
                District(
                    id=district_id,
                    name=district.name,
                    areas=district.get_areas(all_areas),
                    output=district.output,
                    comments=comments,
                )
            )
        return districts

    @override
    def get_district(self, district_id: str) -> District:
        file_study = self.get_file_study()
        if district_id not in file_study.config.sets:
            raise DistrictNotFound(district_id)
        
        district = file_study.config.sets[district_id]
        all_areas = list(file_study.config.areas)
        comments = file_study.tree.get(["input", "areas", "sets", district_id]).get("comments", "")
        
        return District(
            id=district_id,
            name=district.name,
            areas=district.get_areas(all_areas),
            output=district.output,
            comments=comments,
        )

    @override
    def district_exists(self, district_id: str) -> bool:
        file_study = self.get_file_study()
        return district_id in file_study.config.sets

    @override
    def save_district(self, district: District) -> None:
        # Note: This is a simplified implementation. In practice, you would use commands
        # to ensure proper handling of the district configuration and file system updates.
        # For the DAO pattern implementation, we maintain the existing command-based approach.
        raise NotImplementedError("District saving should be done through command pattern")

    @override
    def delete_district(self, district_id: str) -> None:
        # Note: This is a simplified implementation. In practice, you would use commands
        # to ensure proper handling of the district configuration and file system updates.
        # For the DAO pattern implementation, we maintain the existing command-based approach.
        raise NotImplementedError("District deletion should be done through command pattern")