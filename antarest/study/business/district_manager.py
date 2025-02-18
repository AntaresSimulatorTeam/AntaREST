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

from typing import List

from antarest.core.exceptions import AreaNotFound, DistrictAlreadyExist, DistrictNotFound
from antarest.core.serde import AntaresBaseModel
from antarest.study.business.study_interface import StudyInterface
from antarest.study.business.utils import execute_or_add_commands
from antarest.study.model import Study
from antarest.study.storage.rawstudy.model.filesystem.config.identifier import transform_name_to_id
from antarest.study.storage.storage_service import StudyStorageService
from antarest.study.storage.variantstudy.model.command.create_district import CreateDistrict, DistrictBaseFilter
from antarest.study.storage.variantstudy.model.command.remove_district import RemoveDistrict
from antarest.study.storage.variantstudy.model.command.update_district import UpdateDistrict
from antarest.study.storage.variantstudy.model.command_context import CommandContext


class DistrictUpdateDTO(AntaresBaseModel):
    #: Indicates whether this district is used in the output (usually all
    #: districts are visible, but the user can decide to hide some of them).
    output: bool
    #: User-defined comments.
    comments: str = ""
    #: List of areas that will be grouped in the district.
    areas: List[str]


class DistrictCreationDTO(DistrictUpdateDTO):
    #: Name of the district (this name is also used as a unique identifier).
    name: str


class DistrictInfoDTO(DistrictCreationDTO):
    #: District identifier (based on the district name)
    id: str


class DistrictManager:
    """
    Manage districts of a study in order to display consolidated
    data on a group of areas (sum/average of variables).

    It is possible to create new districts composed of several areas, to update or remove districts.

    This class updates the `input/areas/sets.ini` file of the study working directory.
    """

    def __init__(self, command_context: CommandContext):
        self._command_context = command_context

    def get_districts(self, study: StudyInterface) -> List[DistrictInfoDTO]:
        """
        Get the list of districts defined in this study.

        Args:
            study: Study selected from the database.

        Returns:
            The (unordered) list of Data Transfer Objects (DTO) representing districts.
        """
        file_study = study.get_files()
        all_areas = list(file_study.config.areas)
        districts = []
        for district_id, district in file_study.config.sets.items():
            assert district.name is not None
            districts.append(
                DistrictInfoDTO(
                    id=district_id,
                    name=district.name,
                    areas=district.get_areas(all_areas),
                    output=district.output,
                    comments=file_study.tree.get(["input", "areas", "sets", district_id]).get("comments", ""),
                )
            )
        return districts

    def create_district(
        self,
        study: StudyInterface,
        dto: DistrictCreationDTO,
    ) -> DistrictInfoDTO:
        """
        Create a new district in the study and possibly attach areas to it.

        Args:
            study: Study selected from the database.
            dto: Data Transfer Objects (DTO) used for creation.

        Returns:
            the Data Transfer Objects (DTO) representing the newly created district.

        Raises:
            DistrictAlreadyExist: exception raised when district already exists (duplicate).
            AreaNotFound: exception raised when one (or more) area(s) don't exist in the study.
        """
        file_study = study.get_files()
        district_id = transform_name_to_id(dto.name)
        if district_id in file_study.config.sets:
            raise DistrictAlreadyExist(district_id)
        areas = frozenset(dto.areas or [])
        all_areas = frozenset(file_study.config.areas)
        if invalid_areas := areas - all_areas:
            raise AreaNotFound(*invalid_areas)
        command = CreateDistrict(
            name=dto.name,
            output=dto.output,
            comments=dto.comments,
            base_filter=DistrictBaseFilter.remove_all,
            filter_items=list(areas),
            command_context=self._command_context,
            study_version=study.version,
        )
        study.add_commands([command])
        return DistrictInfoDTO(
            id=district_id,
            name=dto.name,
            areas=list(areas),
            output=dto.output,
            comments=dto.comments,
        )

    def update_district(
        self,
        study: StudyInterface,
        district_id: str,
        dto: DistrictUpdateDTO,
    ) -> None:
        """
        Update the properties of a district and/or the areas list.

        Note:
            the `name` can't be updated because it is used as a unique identifier.

        Args:
            study: Study selected from the database.
            district_id: district identifier
            dto: Data Transfer Objects (DTO) used for update.

        Raises:
            DistrictNotFound: exception raised when district is not found in the study.
            AreaNotFound: exception raised when one (or more) area(s) don't exist in the study.
        """
        file_study = study.get_files()
        if district_id not in file_study.config.sets:
            raise DistrictNotFound(district_id)
        areas = set(dto.areas or [])
        all_areas = set(file_study.config.areas)
        if invalid_areas := areas - all_areas:
            raise AreaNotFound(*invalid_areas)
        command = UpdateDistrict(
            id=district_id,
            base_filter=DistrictBaseFilter.remove_all,
            filter_items=dto.areas or [],
            output=dto.output,
            comments=dto.comments,
            command_context=self._command_context,
            study_version=study.version,
        )
        study.add_commands([command])

    def remove_district(
        self,
        study: StudyInterface,
        district_id: str,
    ) -> None:
        """
        Remove a district from a study.

        Args:
            study: Study selected from the database.
            district_id: district identifier

        Raises:
            DistrictNotFound: exception raised when district is not found in the study.
        """
        file_study = study.get_files()
        if district_id not in file_study.config.sets:
            raise DistrictNotFound(district_id)
        command = RemoveDistrict(
            id=district_id,
            command_context=self._command_context,
            study_version=study.version,
        )
        study.add_commands([command])
