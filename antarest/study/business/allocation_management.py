from typing import List

from antarest.core.exceptions import (
    AllocationDataNotFound,
    InvalidAllocationData,
)
from antarest.study.business.area_management import AreaInfoDTO
from antarest.study.business.utils import (
    FormFieldsBaseModel,
    execute_or_add_commands,
)
from antarest.study.model import Study
from antarest.study.storage.storage_service import StudyStorageService
from antarest.study.storage.variantstudy.model.command.update_config import (
    UpdateConfig,
)
from pydantic import NonNegativeFloat


class AllocationField(FormFieldsBaseModel):
    """Consumption coefficient of a given area."""

    area_id: str
    coefficient: NonNegativeFloat


class AllocationFormFields(FormFieldsBaseModel):
    """
    Hydraulic allocation of a production area:
    electrical energy consumption coefficients to consider for each area.
    """

    allocation: List[AllocationField]


class AllocationManager:
    """
    Provides functionality for getting and updating hydraulic allocation
    coefficients for a given production area.
    """

    def __init__(self, storage_service: StudyStorageService) -> None:
        self.storage_service = storage_service

    def get_field_values(
        self, all_areas: List[AreaInfoDTO], study: Study, area_id: str
    ) -> AllocationFormFields:
        """
        Get the hydraulic allocation table of the given production area.

        Get, for a given production area, the electrical energy consumption
        coefficients to consider for the other areas.
        Those values are used to fill in the allocation table form.

        Args:
            study: the current study
            area_id: Production area ID from which we want to retrieve the allocation table.
            all_areas: The complete list of study areas.

        Returns:
            Hydraulic allocation of the production area:
            The list of electrical energy consumption coefficients
            to consider for each area.

        Raises:
            AllocationDataNotFound: exception raised if no hydraulic allocation
            is defined for the given production area (the `.ini` file may be missing).
        """
        file_study = self.storage_service.get_storage(study).get_raw(study)
        allocation_data = file_study.tree.get(
            f"input/hydro/allocation/{area_id}".split("/"), depth=2
        )
        if not allocation_data:
            raise AllocationDataNotFound(area_id)

        areas_ids = {area.id for area in all_areas}
        area, values = allocation_data.popitem()

        return AllocationFormFields.construct(
            allocation=[
                AllocationField.construct(areaId=area, coefficient=value)
                for area, value in values.items()
                if area in areas_ids  # filter invalid areas
            ]
        )

    def set_field_values(
        self,
        all_areas: List[AreaInfoDTO],
        study: Study,
        area_id: str,
        data: AllocationFormFields,
    ) -> None:
        """
        Update the hydraulic allocation table of the given production area.

        Args:
            study: the current study
            area_id: Production area ID from which we want to retrieve the allocation table.
            all_areas: The complete list of study areas.
            data: Hydraulic allocation of the production area:
                The list of electrical energy consumption coefficients
                to consider for each area.

        Raises:
            InvalidAllocationData: exception raised if at least one area
            of the hydraulic allocation table is not an existing area.
        """
        allocation_ids = {field.area_id for field in data.allocation}
        areas_ids = {area.id for area in all_areas}
        if invalid_ids := allocation_ids - areas_ids:
            raise InvalidAllocationData(invalid_ids)

        command_context = (
            self.storage_service.variant_study_service.command_factory.command_context
        )
        command = UpdateConfig(
            target=f"input/hydro/allocation/{area_id}/[allocation]",
            data={f.area_id: f.coefficient for f in data.allocation},
            command_context=command_context,
        )

        file_study = self.storage_service.get_storage(study).get_raw(study)
        execute_or_add_commands(
            study, file_study, [command], self.storage_service
        )
