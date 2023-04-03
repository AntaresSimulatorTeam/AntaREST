from typing import List, Dict

import numpy as np
from antarest.core.exceptions import (
    AllocationDataNotFound,
    AreaNotFound,
    MultipleAllocationDataFound,
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
from pydantic import NonNegativeFloat, validator, BaseModel, conlist


class AllocationField(FormFieldsBaseModel):
    """Consumption coefficient of a given area."""

    class Config:
        allow_population_by_field_name = True
        extra = "forbid"

    area_id: str
    coefficient: NonNegativeFloat


class AllocationFormFields(FormFieldsBaseModel):
    """
    Hydraulic allocation of a production area:
    electrical energy consumption coefficients to consider for each area.
    """

    class Config:
        extra = "forbid"

    allocation: List[AllocationField]

    # noinspection PyMethodParameters
    @validator("allocation")
    def validate_hydro_allocation_column(
        cls, fields: List[AllocationField]
    ) -> List[AllocationField]:
        """
        Validate hydraulic allocation column.

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
            raise ValueError("ensure coefficients colum is non-empty")
        elif np.any(array == 0):
            raise ValueError("ensure coefficients column is not nul")
        else:
            return fields


class AllocationMatrix(BaseModel):
    """
    Hydraulic allocation matrix.

    Data frame matrix, where:

    - `columns`: is the list of selected production areas (given by `area_id`),
    - `index`: is the list of all study areas,
    - `data`: is the 2D-array matrix of consumption coefficients.
    """

    class Config:
        allow_population_by_field_name = True
        extra = "forbid"

    index: conlist(str, min_items=1)  # type: ignore
    columns: conlist(str, min_items=1)  # type: ignore
    data: List[List[float]]  # NonNegativeFloat not necessary

    # noinspection PyMethodParameters
    @validator("data")
    def validate_hydro_allocation_table(
        cls, data: List[List[float]], values: Dict[str, List[str]]
    ) -> List[List[float]]:
        """
        Validate hydraulic allocation table.

        Args:
            data: Hydraulic allocation matrix containing
                the coefficients to be validated.
            values: a dict containing the name-to-value mapping
                of the `index` and `columns` fields (if they are validated).
            values: dictionary that maps names to corresponding fields.
                If the `index` and `columns` fields are validated,
                they are included in this dictionary.

        Raises:
            ValueError:
                If the coefficients columns are empty or has no non-null values.

        Returns:
            The allocation fields.
        """
        array = np.array(data)
        rows = len(values["index"]) if "index" in values else 0
        cols = len(values["columns"]) if "columns" in values else 0
        if array.size == 0:
            raise ValueError("ensure coefficients matrix is a non-empty array")
        elif array.shape != (rows, cols):
            raise ValueError(
                f"ensure coefficients matrix is an array of shape {rows}×{cols}"
            )
        elif np.any(array < 0):
            raise ValueError(
                "ensure coefficients matrix has positive or nul coefficients"
            )
        elif np.any(array.sum(axis=0) == 0):
            raise ValueError("ensure coefficients matrix has non-nul columns")
        else:
            return data


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
        allocation_cfg = file_study.tree.get(
            f"input/hydro/allocation/{area_id}".split("/"), depth=2
        )
        if not allocation_cfg:
            raise AllocationDataNotFound(area_id)
        elif len(allocation_cfg) == 1:
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
            allocations = allocation_data["[allocation]"]
            areas_ids = {area.id for area in all_areas}
            return AllocationFormFields.construct(
                allocation=[
                    # IMPORTANT: use snake_case args because validation is not called,
                    # so field names aliasing is not done.
                    # NOTE: the conversion to JSON uses camelCase names (aliases).
                    AllocationField.construct(area_id=area, coefficient=value)
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
            area_id: Production area ID from which we want to update the allocation table.
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
            raise AreaNotFound(*invalid_ids)
        elif area_id not in areas_ids:
            raise AreaNotFound(area_id)

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
