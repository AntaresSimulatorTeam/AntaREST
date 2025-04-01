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

from typing import Dict, List, Union

import numpy
import numpy as np
from annotated_types import Len
from pydantic import ValidationInfo, field_validator, model_validator
from typing_extensions import Annotated

from antarest.core.exceptions import AllocationDataNotFound, AreaNotFound
from antarest.study.business.model.area_model import AreaInfoDTO
from antarest.study.business.study_interface import StudyInterface
from antarest.study.business.utils import FormFieldsBaseModel
from antarest.study.storage.variantstudy.model.command.update_config import UpdateConfig
from antarest.study.storage.variantstudy.model.command_context import CommandContext


class AllocationField(FormFieldsBaseModel):
    """Model for consumption coefficients of a given area."""

    area_id: str
    coefficient: float


class AllocationFormFields(FormFieldsBaseModel):
    """Model for a list of consumption coefficients for each area."""

    allocation: List[AllocationField]

    @model_validator(mode="after")
    def check_allocation(self) -> "AllocationFormFields":
        allocation = self.allocation

        if not allocation:
            raise ValueError("allocation must not be empty")

        if len(allocation) != len({a.area_id for a in allocation}):
            raise ValueError("allocation must not contain duplicate area IDs")

        for a in allocation:
            if a.coefficient < 0:
                raise ValueError("allocation must not contain negative coefficients")

            if numpy.isnan(a.coefficient):
                raise ValueError("allocation must not contain NaN coefficients")

        if sum(a.coefficient for a in allocation) <= 0:
            raise ValueError("sum of allocation coefficients must be positive")

        return self


class AllocationMatrix(FormFieldsBaseModel):
    """
    Hydraulic allocation matrix.
    index: List of all study areas
    columns: List of selected production areas
    data: 2D-array matrix of consumption coefficients
    """

    index: Annotated[List[str], Len(min_length=1)]
    columns: Annotated[List[str], Len(min_length=1)]
    data: List[List[float]]  # NonNegativeFloat not necessary

    # noinspection PyMethodParameters
    @field_validator("data", mode="before")
    def validate_hydro_allocation_matrix(
        cls, data: List[List[float]], values: Union[Dict[str, List[str]], ValidationInfo]
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
        new_values = values if isinstance(values, dict) else values.data
        rows = len(new_values.get("index", []))
        cols = len(new_values.get("columns", []))

        if array.size == 0:
            raise ValueError("allocation matrix must not be empty")
        if array.shape != (rows, cols):
            raise ValueError("allocation matrix must have square shape")
        if np.any(array < 0):
            raise ValueError("allocation matrix must not contain negative coefficients")
        if np.any(np.isnan(array)):
            raise ValueError("allocation matrix must not contain NaN coefficients")
        if np.all(array == 0):
            raise ValueError("allocation matrix must not contain only null values")

        return data


class AllocationManager:
    """
    Manage hydraulic allocation coefficients.
    """

    def __init__(self, command_context: CommandContext) -> None:
        self._command_context = command_context

    def get_allocation_data(self, study: StudyInterface, area_id: str) -> Dict[str, float]:
        """
        Get hydraulic allocation data.

        Args:
            study: study to get the allocation data from.
            area_id: area to get the allocation data from.

        Returns:
            The allocation data.

        Raises:
            AllocationDataNotFound: if the allocation data is not found.
        """
        # sourcery skip: reintroduce-else, swap-if-else-branches, use-named-expression

        file_study = study.get_files()
        allocation_data = file_study.tree.get(f"input/hydro/allocation/{area_id}".split("/"), depth=2)

        if not allocation_data:
            raise AllocationDataNotFound(area_id)

        # allocation format can differ from the number of '[' (i.e. [[allocation]] or [allocation])
        return allocation_data.get("[allocation]", allocation_data.get("allocation", {}))  # type: ignore

    def get_allocation_form_fields(
        self, all_areas: List[AreaInfoDTO], study: StudyInterface, area_id: str
    ) -> AllocationFormFields:
        """
        Get hydraulic allocation coefficients.

        Args:
            all_areas: list of all areas in the study.
            study: study to get the allocation coefficients from.
            area_id: area to get the allocation coefficients from.

        Returns:
            The allocation coefficients.

        Raises:
            AllocationDataNotFound: if the allocation data is not found.
        """

        areas_ids = {area.id for area in all_areas}
        allocations: Dict[str, float] = self.get_allocation_data(study, area_id)

        filtered_allocations = {area: value for area, value in allocations.items() if area in areas_ids}
        final_allocations = [
            AllocationField.model_construct(area_id=area, coefficient=value)
            for area, value in filtered_allocations.items()
        ]
        return AllocationFormFields.model_validate({"allocation": final_allocations})

    def set_allocation_form_fields(
        self,
        all_areas: List[AreaInfoDTO],
        study: StudyInterface,
        area_id: str,
        data: AllocationFormFields,
    ) -> AllocationFormFields:
        """
        Set hydraulic allocation coefficients.

        Args:
            all_areas: list of all areas in the study.
            study: study to set the allocation coefficients to.
            area_id: area to set the allocation coefficients to.
            data: allocation coefficients to set.

        Raises:
            AreaNotFound: if the area is not found.
        """

        allocation_ids = {field.area_id for field in data.allocation}
        areas_ids = {area.id for area in all_areas}

        if invalid_ids := allocation_ids - areas_ids:
            # sort for deterministic error message and testing
            raise AreaNotFound(*sorted(invalid_ids))

        filtered_allocations = [f for f in data.allocation if f.coefficient > 0 and f.area_id in areas_ids]

        command = UpdateConfig(
            target=f"input/hydro/allocation/{area_id}/[allocation]",
            data={f.area_id: f.coefficient for f in filtered_allocations},
            command_context=self._command_context,
            study_version=study.version,
        )

        study.add_commands([command])

        updated_allocations = self.get_allocation_data(study, area_id)

        return AllocationFormFields.model_construct(
            allocation=[
                AllocationField.model_construct(area_id=area, coefficient=value)
                for area, value in updated_allocations.items()
            ]
        )

    def get_allocation_matrix(self, study: StudyInterface, all_areas: List[AreaInfoDTO]) -> AllocationMatrix:
        """
        Get the hydraulic allocation matrix for all areas in the study.

        Args:
            study: study to get the allocation matrix from.
            all_areas: list of all areas in the study.

        Returns:
            The allocation matrix.

        Raises:
            AllocationDataNotFound: if the allocation data is not found.
        """

        file_study = study.get_files()
        allocation_cfg = file_study.tree.get(["input", "hydro", "allocation"], depth=3)

        if not allocation_cfg:
            areas_ids = {area.id for area in all_areas}
            raise AllocationDataNotFound(*areas_ids)

        rows = [area.id for area in all_areas]
        columns = [area.id for area in all_areas if area.id in allocation_cfg]
        array = np.zeros((len(rows), len(columns)), dtype=np.float64)

        for prod_area, allocation_dict in allocation_cfg.items():
            # allocation format can differ from the number of '[' (i.e. [[allocation]] or [allocation])
            allocations = allocation_dict.get("[allocation]", allocation_dict.get("allocation", {}))
            for cons_area, coefficient in allocations.items():
                row_idx = rows.index(cons_area)
                col_idx = columns.index(prod_area)
                array[row_idx][col_idx] = coefficient

        return AllocationMatrix.model_construct(index=rows, columns=columns, data=array.tolist())
