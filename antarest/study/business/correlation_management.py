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

"""
Management of spatial correlations between the different generators.
The generators are of the same category and can be hydraulic, wind, load or solar.
"""

import collections
from typing import Dict, List, Sequence, Union

import numpy as np
from pydantic import ValidationInfo, field_validator

from antarest.core.exceptions import AreaNotFound
from antarest.core.serde.np_array import NpArray
from antarest.study.business.model.area_model import AreaInfoDTO
from antarest.study.business.study_interface import StudyInterface
from antarest.study.business.utils import FormFieldsBaseModel
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.model.command.update_config import UpdateConfig
from antarest.study.storage.variantstudy.model.command_context import CommandContext


class AreaCoefficientItem(FormFieldsBaseModel):
    """
    Model for correlation coefficients of a given area.

    Attributes:
        area_id: Area identifier.
        coefficient: correlation coefficients in percentage (-100 <= coefficient <= 100).
    """

    class Config:
        populate_by_name = True

    area_id: str
    coefficient: float


class CorrelationFormFields(FormFieldsBaseModel):
    """
    Model for a list of consumption coefficients for each area.

    Attributes:
        correlation: A list of non-null correlation coefficients in percentage.
    """

    correlation: List[AreaCoefficientItem]

    # noinspection PyMethodParameters
    @field_validator("correlation")
    def check_correlation(cls, correlation: List[AreaCoefficientItem]) -> List[AreaCoefficientItem]:
        if not correlation:
            raise ValueError("correlation must not be empty")
        counter = collections.Counter(field.area_id for field in correlation)
        if duplicates := {id_ for id_, count in counter.items() if count > 1}:
            raise ValueError(f"correlation must not contain duplicate area IDs: {duplicates}")

        array = np.array([a.coefficient for a in correlation], dtype=np.float64)
        if np.any((array < -100) | np.any(array > 100)):
            raise ValueError("percentage must be between -100 and 100")
        if np.any(np.isnan(array)):
            raise ValueError("correlation matrix must not contain NaN coefficients")

        return correlation


class CorrelationMatrix(FormFieldsBaseModel):
    """
    Correlation matrix for hydraulic, wind, load, or solar generators.

    Attributes:
        index: A list of all study areas.
        columns: A list of selected production areas.
        data: A 2D-array matrix of correlation coefficients.
    """

    index: List[str]
    columns: List[str]
    data: List[List[float]]  # NonNegativeFloat not necessary

    @field_validator("index", "columns", mode="before")
    def validate_list_length(cls, values: List[str]) -> List[str]:
        if len(values) == 0:
            raise ValueError("correlation matrix cannot have 0 columns/index")
        return values

    # noinspection PyMethodParameters
    @field_validator("data", mode="before")
    def validate_correlation_matrix(
        cls, data: List[List[float]], values: Union[Dict[str, List[str]], ValidationInfo]
    ) -> List[List[float]]:
        """
        Validates the correlation matrix by checking its shape and range of coefficients.

        Args:
            cls: The `CorrelationMatrix` class.
            data: The correlation matrix to validate.
            values: A dictionary containing the values of `index` and `columns`.

        Returns:
            List[List[float]]: The validated correlation matrix.

        Raises:
            ValueError:
                If the correlation matrix is empty,
                has an incorrect shape,
                is squared but not symmetric,
                or contains coefficients outside the range of -1 to 1
                or NaN coefficients.
        """

        array = np.array(data)
        new_values = values if isinstance(values, dict) else values.data
        rows = len(new_values.get("index", []))
        cols = len(new_values.get("columns", []))

        if array.size == 0:
            raise ValueError("correlation matrix must not be empty")
        if array.shape != (rows, cols):
            raise ValueError(f"correlation matrix must have shape ({rows}×{cols})")
        if np.any((array < -1) | np.any(array > 1)):
            raise ValueError("coefficients must be between -1 and 1")
        if np.any(np.isnan(array)):
            raise ValueError("correlation matrix must not contain NaN coefficients")
        if array.shape[0] == array.shape[1] and not np.array_equal(array, array.T):
            raise ValueError("correlation matrix is not symmetric")

        return data

    class Config:
        json_schema_extra = {
            "example": {
                "columns": ["north", "east", "south", "west"],
                "data": [
                    [0.0, 0.0, 0.25, 0.0],
                    [0.0, 0.0, 0.75, 0.12],
                    [0.25, 0.75, 0.0, 0.75],
                    [0.0, 0.12, 0.75, 0.0],
                ],
                "index": ["north", "east", "south", "west"],
            }
        }


def _config_to_array(
    area_ids: Sequence[str],
    correlation_cfg: Dict[str, str],
) -> NpArray:
    array = np.identity(len(area_ids), dtype=np.float64)
    for key, value in correlation_cfg.items():
        a1, a2 = key.split("%")
        i = area_ids.index(a1)
        j = area_ids.index(a2)
        if i == j:
            # ignored: values from the diagonal are always == 1.0
            continue
        coefficient = value
        array[i][j] = coefficient
        array[j][i] = coefficient
    return array


def _array_to_config(
    area_ids: Sequence[str],
    array: NpArray,
) -> Dict[str, str]:
    correlation_cfg: Dict[str, str] = {}
    count = len(area_ids)
    for i in range(count):
        # not saved: values from the diagonal are always == 1.0
        for j in range(i + 1, count):
            coefficient = array[i][j]
            if not coefficient:
                # null values are not saved
                continue
            a1 = area_ids[i]
            a2 = area_ids[j]
            correlation_cfg[f"{a1}%{a2}"] = coefficient
    return correlation_cfg


class CorrelationManager:
    """
    This manager allows you to read and write the hydraulic, wind, load or solar
    correlation matrices of a raw study or a variant.
    """

    # Today, only the 'hydro' category is fully supported, but
    # we could also manage the 'load' 'solar' and 'wind'
    # categories but the usage is deprecated.
    url = ["input", "hydro", "prepro", "correlation", "annual"]

    def __init__(self, command_context: CommandContext) -> None:
        self._command_context = command_context

    def _get_array(
        self,
        file_study: FileStudy,
        area_ids: Sequence[str],
    ) -> NpArray:
        try:
            correlation_cfg = file_study.tree.get(self.url, depth=3)
        except KeyError:
            # some studies could not have an annual field
            # make sure the other fields exist
            assert file_study.tree.get(self.url[:-1])
            correlation_cfg = {}
        return _config_to_array(area_ids, correlation_cfg)

    def _set_array(
        self,
        study: StudyInterface,
        area_ids: Sequence[str],
        array: NpArray,
    ) -> None:
        correlation_cfg = _array_to_config(area_ids, array)
        command = UpdateConfig(
            target="/".join(self.url),
            data=correlation_cfg,
            command_context=self._command_context,
            study_version=study.version,
        )
        study.add_commands([command])

    def get_correlation_form_fields(
        self, all_areas: List[AreaInfoDTO], study: StudyInterface, area_id: str
    ) -> CorrelationFormFields:
        """
        Get the correlation form fields (percentage values) for a given area.

        Args:
            all_areas: list of all areas in the study.
            study: study to get the correlation coefficients from.
            area_id: area to get the correlation coefficients from.

        Returns:
            The correlation coefficients.
        """
        file_study = study.get_files()

        area_ids = [area.id for area in all_areas]
        array = self._get_array(file_study, area_ids)
        column = array[:, area_ids.index(area_id)] * 100

        correlation_field = [
            AreaCoefficientItem.model_construct(area_id=a, coefficient=c)
            for a, c in zip(area_ids, column)
            if a != area_id and c
        ]

        current_area_coefficient = column[area_ids.index(area_id)]
        correlation_field.insert(
            0,
            AreaCoefficientItem.model_construct(area_id=area_id, coefficient=current_area_coefficient),
        )

        return CorrelationFormFields.model_construct(correlation=correlation_field)

    def set_correlation_form_fields(
        self,
        all_areas: List[AreaInfoDTO],
        study: StudyInterface,
        area_id: str,
        data: CorrelationFormFields,
    ) -> CorrelationFormFields:
        """
        Set the correlation coefficients of a given area from the form fields (percentage values).

        Args:
            all_areas: list of all areas in the study.
            study: study to set the correlation coefficients to.
            area_id: area to set the correlation coefficients to.
            data: correlation coefficients to set.

        Raises:
            AreaNotFound: if the area is not found or invalid.

        Returns:
            The updated correlation coefficients.
        """
        area_ids = [area.id for area in all_areas]
        correlation_values = collections.OrderedDict.fromkeys(area_ids, 0.0)
        correlation_values.update({field.area_id: field.coefficient for field in data.correlation})

        if invalid_ids := set(correlation_values) - set(area_ids):
            # sort for deterministic error message and testing
            raise AreaNotFound(*sorted(invalid_ids))

        file_study = study.get_files()
        array = self._get_array(file_study, area_ids)
        j = area_ids.index(area_id)
        for i, coefficient in enumerate(correlation_values.values()):
            array[i][j] = coefficient / 100
            array[j][i] = coefficient / 100
        self._set_array(study, area_ids, array)

        column = array[:, area_ids.index(area_id)] * 100
        return CorrelationFormFields.model_construct(
            correlation=[
                AreaCoefficientItem.model_construct(area_id=a, coefficient=c) for a, c in zip(area_ids, column) if c
            ]
        )

    def get_correlation_matrix(
        self, all_areas: List[AreaInfoDTO], study: StudyInterface, columns: List[str]
    ) -> CorrelationMatrix:
        """
        Read the correlation coefficients and get the correlation matrix (values in the range -1 to 1).

        Args:
            all_areas: list of all areas in the study.
            study: study to get the correlation matrix from.
            columns: areas to get the correlation matrix from.

        Returns:
            The correlation matrix.
        """
        file_study = study.get_files()
        area_ids = [area.id for area in all_areas]
        columns = [a for a in area_ids if a in columns] if columns else area_ids
        array = self._get_array(file_study, area_ids)
        # noinspection PyTypeChecker
        data = [[c for i, c in enumerate(row) if area_ids[i] in columns] for row in array.tolist()]

        return CorrelationMatrix.model_construct(index=area_ids, columns=columns, data=data)

    def set_correlation_matrix(
        self,
        all_areas: List[AreaInfoDTO],
        study: StudyInterface,
        matrix: CorrelationMatrix,
    ) -> CorrelationMatrix:
        """
        Set the correlation coefficients from the coefficient matrix (values in the range -1 to 1).

        Args:
            all_areas: list of all areas in the study.
            study: study to get the correlation matrix from.
            matrix: correlation matrix to update

        Returns:
            The updated correlation matrix.
        """
        file_study = study.get_files()
        area_ids = [area.id for area in all_areas]

        array = self._get_array(file_study, area_ids)

        for row, a1 in zip(matrix.data, matrix.index):
            for coefficient, a2 in zip(row, matrix.columns):
                if missing := {a1, a2} - set(area_ids):
                    raise AreaNotFound(*missing)
                i = area_ids.index(a1)
                j = area_ids.index(a2)
                array[i][j] = coefficient
                array[j][i] = coefficient

        self._set_array(study, area_ids, array)

        # noinspection PyTypeChecker
        data = [[c for i, c in enumerate(row) if area_ids[i] in matrix.columns] for row in array.tolist()]

        return CorrelationMatrix.model_construct(index=area_ids, columns=matrix.columns, data=data)
