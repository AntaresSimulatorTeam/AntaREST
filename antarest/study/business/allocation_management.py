from typing import List

import numpy
import numpy as np
from antarest.core.exceptions import AllocationDataNotFound, AreaNotFound, MultipleAllocationDataFound
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
from pydantic import NonNegativeFloat, validator, BaseModel


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

    # noinspection PyMethodParameters
    @validator("allocation")
    def validate_hydro_allocation_table(cls, fields: List[AllocationField]):
        """
        Validate hydraulic allocation table.

        Args:
            fields: A list of validated allocation fields containing
            the coefficients to be validated.

        Raises:
            ValueError:
                If the coefficients array is empty or has no non-null values.

        Returns:
            The allocation fields.
        """
        array = np.array([f.coefficient for f in fields])
        if array.size == 0:
            raise ValueError("coefficients array is empty")
        elif np.any(array == 0):
            raise ValueError("coefficients array has no non-null values")
        else:
            return fields


class AllocationMatrix(BaseModel):
    index: List[str]
    columns: List[str]
    data: List[List[NonNegativeFloat]]


class AllocationManager:
    """
    Provides functionality for getting and updating hydraulic allocation
    coefficients for a given production area.
    """

    def __init__(self, storage_service: StudyStorageService) -> None:
        self.storage_service = storage_service

    def get_allocation_matrix(
        self, all_areas: List[AreaInfoDTO], study: Study, area_id: str
    ) -> AllocationMatrix:
        """
        Get the electrical energy consumption matrix for a given production area,
        a selected list of production areas or all areas.

        Args:
            all_areas: The complete list of study areas.
            study: the current study
            area_id:
                A production area ID (e.g.: 'EAST'),
                a comma-separated list of production area IDs (e.g.: 'EAST,SOUTH'),
                or all areas using the star symbol (e.g.: '*').

        Returns:
            Returns the data frame matrix, where:

            - `columns`: is the list of selected production areas (given by `area_id`),
            - `index`: is the list of all study areas,
            - `data`: is the 2D-array matrix of consumption coefficients.

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
        rows = sorted(area.id for area in all_areas)
        columns = sorted(allocation_data)
        array = numpy.zeros((len(rows), len(columns)), dtype=numpy.float)
        for prod_area, allocation_dict in allocation_data.items():
            allocations = allocation_dict["[allocation]"]
            for cons_area, coefficient in allocations.items():
                row_idx = rows.index(cons_area)
                col_idx = columns.index(prod_area)
                array[row_idx][col_idx] = coefficient
        return AllocationMatrix.construct(
            index=rows, columns=columns, data=array.tolist()
        )

    def get_field_values(
        self, all_areas: List[AreaInfoDTO], study: Study, area_id: str
    ) -> AllocationFormFields:
        """
        Get the hydraulic allocation table of the given production area (or areas).

        Args:
            all_areas: The complete list of study areas.
            study: the current study
            area_id: A production area ID (e.g.: 'EAST').

        Returns:
            Hydraulic allocation of the production area:
            The list of electrical energy consumption coefficients
            to consider for each area.

        Raises:
            MultipleAllocationDataFound: exception raised if no hydraulic allocation
            is defined for the given production area (the `.ini` file may be missing),
            or if several production areas are requested.
        """
        file_study = self.storage_service.get_storage(study).get_raw(study)
        allocation_data = file_study.tree.get(
            f"input/hydro/allocation/{area_id}".split("/"), depth=2
        )
        if len(allocation_data) == 1:
            # single-column allocation table
            areas_ids = {area.id for area in all_areas}
            allocations = allocation_data["[allocation]"]
            return AllocationFormFields.construct(
                allocation=[
                    AllocationField.construct(areaId=area, coefficient=value)
                    for area, value in allocations.items()
                    if area in areas_ids  # filter invalid areas
                ]
            )
        raise MultipleAllocationDataFound(*allocation_data)

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
            AreaNotFound: exception raised if at least one area
            of the hydraulic allocation table is not an existing area.
        """
        allocation_ids = {field.area_id for field in data.allocation}
        areas_ids = {area.id for area in all_areas}
        if invalid_ids := allocation_ids - areas_ids:
            # sorting is mandatory for unit tests
            raise AreaNotFound(*sorted(invalid_ids))

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
