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

from typing import Sequence

from antarest.core.exceptions import AreaNotFound, DistrictAlreadyExist, DistrictNotFound
from antarest.study.business.model.district_model import (
    DistrictCreation,
    DistrictDTO,
    DistrictUpdate,
    create_district,
)
from antarest.study.business.study_interface import StudyInterface
from antarest.study.storage.rawstudy.model.filesystem.config.identifier import transform_name_to_id
from antarest.study.storage.variantstudy.model.command.create_district import CreateDistrict
from antarest.study.storage.variantstudy.model.command.remove_district import RemoveDistrict
from antarest.study.storage.variantstudy.model.command.update_district import UpdateDistrict
from antarest.study.storage.variantstudy.model.command_context import CommandContext


class DistrictManager:
    """
    Manage districts of a study in order to display consolidated
    data on a group of areas (sum/average of variables).

    It is possible to create new districts composed of several areas, to update or remove districts.

    This class updates the `input/areas/sets.ini` file of the study working directory.
    """

    def __init__(self, command_context: CommandContext):
        self._command_context = command_context

    def get_districts(self, study: StudyInterface) -> Sequence[DistrictDTO]:
        """
        Get the list of districts defined in this study.

        Args:
            study: Study from the database.

        Returns:
            The (unordered) list of districts.
        """
        all_areas = study.get_study_dao().tmp_get_all_areas()
        return [district.to_dto(all_areas) for district in study.get_study_dao().get_districts()]

    def create_district(
        self,
        study: StudyInterface,
        district_creation: DistrictCreation,
    ) -> DistrictDTO:
        """
        Create a new district in the study and possibly attach areas to it.

        Args:
            study: Study selected from the database.
            district_creation: Content of the creation.

        Returns:
            The newly created district.

        Raises:
            DistrictAlreadyExist: exception raised when district already exists (duplicate).
            AreaNotFound: exception raised when one (or more) area(s) don't exist in the study.
        """
        study_dao = study.get_study_dao()
        district_id = transform_name_to_id(district_creation.name)
        if study_dao.district_exists(district_id):
            raise DistrictAlreadyExist(district_id)

        invalid_areas = study_dao.get_invalid_areas_in_district(district_creation.areas or [])
        if invalid_areas:
            raise AreaNotFound(*invalid_areas)

        command = CreateDistrict(
            parameters=district_creation,
            command_context=self._command_context,
            study_version=study.version,
        )
        study.add_commands([command])
        all_areas = study_dao.tmp_get_all_areas()
        return create_district(district_creation, district_id).to_dto(all_areas)  #

    def update_district(
        self,
        study: StudyInterface,
        district_id: str,
        district_update: DistrictUpdate,
    ) -> None:
        """
        Update the properties of a district and/or the areas list.

        Note:
            the `name` can't be updated because it is used as a unique identifier.

        Args:
            study: Study selected from the database.
            district_id: district identifier
            district_update: content of the update.

        Raises:
            DistrictNotFound: exception raised when district is not found in the study.
            AreaNotFound: exception raised when one (or more) area(s) don't exist in the study.
        """
        study_dao = study.get_study_dao()
        if not study_dao.district_exists(district_id):
            raise DistrictNotFound(district_id)

        invalid_areas = study_dao.get_invalid_areas_in_district(district_update.areas or [])
        if invalid_areas:
            raise AreaNotFound(*invalid_areas)

        command = UpdateDistrict(
            id=district_id,
            parameters=district_update,
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
        study_dao = study.get_study_dao()
        if not study_dao.district_exists(district_id):
            raise DistrictNotFound(district_id)
        command = RemoveDistrict(
            id=district_id,
            command_context=self._command_context,
            study_version=study.version,
        )
        study.add_commands([command])
