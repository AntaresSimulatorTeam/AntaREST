from typing import List, Dict

import numpy
import numpy as np
from pydantic import root_validator
from pydantic import validator, conlist

from antarest.core.exceptions import (
    AllocationDataNotFound,
    AreaNotFound,
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


class AllocationField(FormFieldsBaseModel):
    """Model for consumption coefficients of a given area."""

    area_id: str
    coefficient: float


class AllocationFormFields(FormFieldsBaseModel):
    """Model for a list of consumption coefficients for each area."""

    allocation: List[AllocationField]

    @root_validator
    def check_allocation(
        cls, values: Dict[str, List[AllocationField]]
    ) -> Dict[str, List[AllocationField]]:
        allocation = values.get("allocation", [])

        if not allocation:
            raise ValueError("allocation must not be empty")

        if len(allocation) != len(set(a.area_id for a in allocation)):
            raise ValueError("allocation must not contain duplicate area IDs")

        for a in allocation:
            if a.coefficient < 0:
                raise ValueError(
                    "allocation must not contain negative coefficients"
                )

            if numpy.isnan(a.coefficient):
                raise ValueError(
                    "allocation must not contain NaN coefficients"
                )

        if sum(a.coefficient for a in allocation) <= 0:
            raise ValueError("sum of allocation coefficients must be positive")

        return values


class AllocationMatrix(FormFieldsBaseModel):
    """
    Hydraulic allocation matrix.
    index: List of all study areas
    columns: List of selected production areas
    data: 2D-array matrix of consumption coefficients
    """

    index: conlist(str, min_items=1)  # type: ignore
    columns: conlist(str, min_items=1)  # type: ignore
    data: List[List[float]]  # NonNegativeFloat not necessary

    # noinspection PyMethodParameters
    @validator("data")
    def validate_hydro_allocation_matrix(
        cls, data: List[List[float]], values: Dict[str, List[str]]
    ) -> List[List[float]]:
        """
        Validate the hydraulic allocation matrix.
        Args:
            data: the allocation matrix to validate.
            values: the allocation matrix fields.
        Raises:
            ValueError:
                If the coefficients columns are empty or has no non-null values.
        Returns:
            The allocation fields.
        """

        array = np.array(data)
        rows = len(values.get("index", []))
        cols = len(values.get("columns", []))

        if array.size == 0:
            raise ValueError("allocation matrix must not be empty")
        if array.shape != (rows, cols):
            raise ValueError(f"allocation matrix must have square shape")
        if np.any(array < 0):
            raise ValueError(
                "allocation matrix must not contain negative coefficients"
            )
        if np.any(array.sum(axis=0) == 0):
            raise ValueError(
                "allocation matrix must not contain empty columns"
            )
        if np.any(np.isnan(array)):
            raise ValueError(
                "allocation matrix must not contain NaN coefficients"
            )
        if np.all(array == 0):
            raise ValueError(
                "allocation matrix must not contain only null values"
            )

        return data


class AllocationManager:
    """
    Manage hydraulic allocation coefficients.
    """

    def __init__(self, storage_service: StudyStorageService) -> None:
        self.storage_service = storage_service

    def get_allocation_data(
        self, study: Study, area_id: str
    ) -> Dict[str, List[AllocationField]]:
        """
        Get hydraulic allocation data.

        Args:
            study: study to get the allocation data from
            area_id: area to get the allocation data from

        Returns:
            The allocation data.

        Raises:
            AllocationDataNotFound: if the allocation data is not found.
        """

        file_study = self.storage_service.get_storage(study).get_raw(study)
        allocation_data = file_study.tree.get(
            f"input/hydro/allocation/{area_id}".split("/"), depth=2
        )

        if not allocation_data:
            raise AllocationDataNotFound(area_id)

        return allocation_data.get("[allocation]", {})

    def get_allocation_form_fields(
        self, all_areas: List[AreaInfoDTO], study: Study, area_id: str
    ) -> AllocationFormFields:
        """
        Get hydraulic allocation coefficients.

        Args:
            all_areas: list of all areas in the study
            study: study to get the allocation coefficients from
            area_id: area to get the allocation coefficients from

        Returns:
            The allocation coefficients.

        Raises:
            AllocationDataNotFound: if the allocation data is not found.
        """

        areas_ids = {area.id for area in all_areas}
        allocations = self.get_allocation_data(study, area_id)

        return AllocationFormFields.construct(
            allocation=[
                AllocationField.construct(area_id=area, coefficient=value)
                for area, value in allocations.items()
                if area in areas_ids  # filter invalid areas
            ]
        )

    def set_allocation_form_fields(
        self,
        all_areas: List[AreaInfoDTO],
        study: Study,
        area_id: str,
        data: AllocationFormFields,
    ) -> AllocationFormFields:
        """
        Set hydraulic allocation coefficients.

        Args:
            all_areas: list of all areas in the study
            study: study to set the allocation coefficients to
            area_id: area to set the allocation coefficients to
            data: allocation coefficients to set

        Raises:
            AreaNotFound: if the area is not found.
        """

        allocation_ids = {field.area_id for field in data.allocation}
        areas_ids = {area.id for area in all_areas}

        if invalid_ids := allocation_ids - areas_ids:
            # sort for deterministic error message and testing
            raise AreaNotFound(*sorted(invalid_ids))

        filtered_allocations = [
            f
            for f in data.allocation
            if f.coefficient > 0 and f.area_id in areas_ids
        ]

        command_context = (
            self.storage_service.variant_study_service.command_factory.command_context
        )
        command = UpdateConfig(
            target=f"input/hydro/allocation/{area_id}/[allocation]",
            data={f.area_id: f.coefficient for f in filtered_allocations},
            command_context=command_context,
        )

        file_study = self.storage_service.get_storage(study).get_raw(study)

        execute_or_add_commands(
            study, file_study, [command], self.storage_service
        )

        updated_allocations = self.get_allocation_data(study, area_id)

        return AllocationFormFields.construct(
            allocation=[
                AllocationField.construct(area_id=area, coefficient=value)
                for area, value in updated_allocations.items()
            ]
        )

    def get_allocation_matrix(
        self, all_areas: List[AreaInfoDTO], study: Study, area_id: str
    ) -> AllocationMatrix:
        """
        Get the hydraulic allocation matrix.

        Args:
            all_areas: list of all areas in the study
            study: study to get the allocation matrix from
            area_id: area to get the allocation matrix from

        Returns:
            The allocation matrix.

        Raises:
            AllocationDataNotFound: if the allocation data is not found.
        """
        file_study = self.storage_service.get_storage(study).get_raw(study)
        allocation_cfg = file_study.tree.get(
            f"input/hydro/allocation/{area_id}".split("/"), depth=2
        )
        if not allocation_cfg:
            raise AllocationDataNotFound(area_id)
        elif len(allocation_cfg) == 1:
            # IMPORTANT: when there is only one element left the function returns
            # the allocation of the element in place of the dictionary by zone
            allocation_cfg = {area_id: allocation_cfg}
        # Preserve the order of `all_areas`
        rows = [area.id for area in all_areas]
        # IMPORTANT: keep the same order for columns
        columns = [area.id for area in all_areas if area.id in allocation_cfg]
        array = np.zeros((len(rows), len(columns)), dtype=np.float64)
        for prod_area, allocation_dict in allocation_cfg.items():
            allocations = allocation_dict["[allocation]"]
            for cons_area, coefficient in allocations.items():
                row_idx = rows.index(cons_area)
                col_idx = columns.index(prod_area)
                array[row_idx][col_idx] = coefficient
        return AllocationMatrix.construct(
            index=rows, columns=columns, data=array.tolist()
        )
