from typing import List

from pydantic import NonNegativeFloat
from starlette.responses import JSONResponse

from antarest.core.exceptions import AllocationDataNotFound, InvalidAllocationData
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


class AllocationField(FormFieldsBaseModel):
    area_id: str
    coefficient: NonNegativeFloat


class AllocationFormFields(FormFieldsBaseModel):
    allocation: List[AllocationField]


class AllocationManager:
    """
    Provides functionality for getting and updating allocation fields for a given area
    """

    def __init__(self, storage_service: StudyStorageService) -> None:
        self.storage_service = storage_service

    def get_field_values(
            self, study: Study, area_id: str, all_areas
    ) -> AllocationFormFields:
        file_study = self.storage_service.get_storage(study).get_raw(study)
        allocation_data = file_study.tree.get(
            f"input/hydro/allocation/{area_id}".split("/"), 2
        )

        areas_ids = [area.id for area in all_areas]

        if not allocation_data:
            raise AllocationDataNotFound(area_id)

        area, values = allocation_data.popitem()

        allocation_fields = AllocationFormFields(
            allocation=[
                AllocationField.construct(areaId=area, coefficient=value)
                for area, value in values.items()
                if area in areas_ids  # filter invalid areas
            ]
        )

        return allocation_fields

    def set_field_values(
            self,
            study: Study,
            area_id: str,
            data: AllocationFormFields,
            all_areas: List[AreaInfoDTO],
    ) -> None:
        """
        Sets allocation fields for a given area
        """
        areas_ids = [area.id for area in all_areas]
        allocation_ids = [field.area_id for field in data.allocation]

        if invalid_ids := set(allocation_ids) - set(areas_ids):
            return InvalidAllocationData(invalid_ids)

        command_context = (
            self.storage_service.variant_study_service.command_factory.command_context
        )
        command = UpdateConfig(
            target=f"input/hydro/allocation/{area_id}/[allocation]",
            data={
                field.area_id: float(field.coefficient)
                for field in data.allocation
            },
            command_context=command_context,
        )

        file_study = self.storage_service.get_storage(study).get_raw(study)
        execute_or_add_commands(
            study, file_study, [command], self.storage_service
        )
