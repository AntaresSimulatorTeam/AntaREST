from typing import List, Optional, Iterable

from pydantic import BaseModel

from antarest.core.exceptions import (
    AreaNotFound,
    DistrictAlreadyExist,
    DistrictNotFound,
)
from antarest.study.business.utils import execute_or_add_commands
from antarest.study.model import Study
from antarest.study.storage.rawstudy.model.filesystem.config.model import (
    transform_name_to_id,
)
from antarest.study.storage.storage_service import StudyStorageService
from antarest.study.storage.variantstudy.model.command.create_district import (
    CreateDistrict,
    DistrictBaseFilter,
)
from antarest.study.storage.variantstudy.model.command.remove_district import (
    RemoveDistrict,
)
from antarest.study.storage.variantstudy.model.command.update_district import (
    UpdateDistrict,
)


class DistrictInfoDTO(BaseModel):
    id: str
    name: str
    areas: List[str]
    output: bool
    comments: str = ""


class DistrictManager:
    """
    Manage districts of a study in order to display consolidated
    data on a group of areas (sum/average of variables).

    It is possible to create new districts composed of several areas, to update or remove districts.

    This class updates the `input/areas/sets.ini` file of the study working directory.
    """

    def __init__(self, storage_service: StudyStorageService):
        self.storage_service = storage_service

    def get_districts(self, study: Study) -> List[DistrictInfoDTO]:
        """
        Get the list of districts defined in this study.

        Args:
            study: Study selected from the database.

        Returns:
            The (unordered) list of Data Transfer Objects (DTO) representing districts.
        """
        file_study = self.storage_service.get_storage(study).get_raw(study)
        all_areas = list(file_study.config.areas)
        return [
            DistrictInfoDTO(
                id=district_id,
                name=district.name,
                areas=district.get_areas(all_areas),
                output=district.output,
                comments=file_study.tree.get(
                    ["input", "areas", "sets", district_id]
                ).get("comments", ""),
            )
            for district_id, district in file_study.config.sets.items()
        ]

    def create_district(
        self,
        study: Study,
        name: str,
        output: bool,
        comments: str,
        areas: Optional[Iterable[str]] = None,
    ) -> DistrictInfoDTO:
        """
        Create a new district in the study and possibly attach areas to it.

        Args:
            study: Study selected from the database.
            name: name of the district (this name is also used as a unique identifier).
            output:
                Indicates whether this district is used in the output (usually all
                districts are visible, but the user can decide to hide some of them).
            comments: used-defined comments.
            areas: optional list of areas that will be grouped in the district.

        Returns:
            the Data Transfer Objects (DTO) representing the newly created district.

        Raises:
            DistrictAlreadyExist: exception raised when district already exists (duplicate).
            AreaNotFound: exception raised when one (or more) area(s) don't exist in the study.
        """
        file_study = self.storage_service.get_storage(study).get_raw(study)
        district_id = transform_name_to_id(name)
        if district_id in file_study.config.sets:
            raise DistrictAlreadyExist(district_id)
        areas = frozenset(areas or [])
        all_areas = frozenset(file_study.config.areas)
        if invalid_areas := areas - all_areas:
            raise AreaNotFound(*invalid_areas)
        command = CreateDistrict(
            name=name,
            output=output,
            comments=comments,
            base_filter=DistrictBaseFilter.remove_all,
            filter_items=areas,
            command_context=self.storage_service.variant_study_service.command_factory.command_context,
        )
        execute_or_add_commands(
            study, file_study, [command], self.storage_service
        )
        return DistrictInfoDTO(
            id=district_id,
            name=name,
            areas=list(areas),
            output=output,
            comments=comments,
        )

    def update_district(
        self,
        study: Study,
        district_id: str,
        output: bool,
        comments: str,
        areas: Optional[Iterable[str]] = None,
    ) -> None:
        """
        Update the properties of a district and/or the areas list.

        Note:
            the `name` can't be updated because it is used as a unique identifier.

        Args:
            study: Study selected from the database.
            district_id: district identifier
            output:
                Indicates whether this district is used in the output (usually all
                districts are visible, but the user can decide to hide some of them).
            comments: used-defined comments.
            areas: optional list of areas that will be grouped in the district.

        Raises:
            DistrictNotFound: exception raised when district is not found in the study.
            AreaNotFound: exception raised when one (or more) area(s) don't exist in the study.
        """
        file_study = self.storage_service.get_storage(study).get_raw(study)
        if district_id not in file_study.config.sets:
            raise DistrictNotFound(district_id)
        areas = frozenset(areas or [])
        all_areas = frozenset(file_study.config.areas)
        if invalid_areas := areas - all_areas:
            raise AreaNotFound(*invalid_areas)
        command = UpdateDistrict(
            id=district_id,
            base_filter=DistrictBaseFilter.remove_all,
            filter_items=areas,
            output=output,
            comments=comments,
            command_context=self.storage_service.variant_study_service.command_factory.command_context,
        )
        execute_or_add_commands(
            study, file_study, [command], self.storage_service
        )

    def remove_district(
        self,
        study: Study,
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
        file_study = self.storage_service.get_storage(study).get_raw(study)
        if district_id not in file_study.config.sets:
            raise DistrictNotFound(district_id)
        command = RemoveDistrict(
            id=district_id,
            command_context=self.storage_service.variant_study_service.command_factory.command_context,
        )
        execute_or_add_commands(
            study, file_study, [command], self.storage_service
        )
