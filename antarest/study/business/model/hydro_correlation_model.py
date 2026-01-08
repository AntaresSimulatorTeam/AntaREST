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
from typing import Annotated, TypeAlias

import numpy as np
from pydantic import Field, PlainSerializer, model_validator
from pydantic.alias_generators import to_camel

from antarest.core.serde import AntaresBaseModel
from antarest.core.serde.np_array import NpArray


class HydroCorrelationArea(AntaresBaseModel, extra="forbid", populate_by_name=True, alias_generator=to_camel):
    area_id: str
    coefficient: float = Field(allow_inf_nan=False, ge=-100, le=100)


def _correlation_serializer(correlation: list[HydroCorrelationArea]) -> list[dict[str, str | float]]:
    return [corr.model_dump(by_alias=True) for corr in sorted(correlation, key=lambda c: c.area_id) if corr.coefficient]


HydroCorrelationType: TypeAlias = Annotated[list[HydroCorrelationArea], PlainSerializer(_correlation_serializer)]


class HydroCorrelation(AntaresBaseModel, extra="forbid", populate_by_name=True):
    correlation: HydroCorrelationType

    @model_validator(mode="after")
    def check_correlation(self) -> "HydroCorrelation":
        correlation = self.correlation

        if not correlation:
            raise ValueError("correlation must not be empty")

        if len(correlation) != len({a.area_id for a in correlation}):
            raise ValueError("correlation must not contain duplicate area IDs")

        return self


class HydroCorrelationMatrix(AntaresBaseModel, extra="forbid", populate_by_name=True, arbitrary_types_allowed=True):
    """
    Hydraulic correlation matrix.
    index: List of all study areas
    columns: List of selected production areas
    data: A 2D-array matrix of correlation coefficients.
    """

    index: list[str]
    columns: list[str]
    data: NpArray

    @model_validator(mode="after")
    def check_model(self) -> "HydroCorrelationMatrix":
        return self._validate_model()

    def _validate_model(self) -> "HydroCorrelationMatrix":
        if self.data.size == 0:
            raise ValueError("correlation matrix must not be empty")

        if self.index != self.columns:
            raise ValueError("correlation matrix must have the same rows and columns")

        if np.any((self.data < -1) | (self.data > 1)):
            raise ValueError("coefficients must be between -1 and 1")

        if np.any(np.isnan(self.data)):
            raise ValueError("correlation matrix must not contain NaN coefficients")

        n = len(self.index)
        if self.data.shape != (n, n):
            raise ValueError(f"correlation matrix must have shape ({n}×{n})")

        if not np.array_equal(self.data, self.data.T):
            raise ValueError("correlation matrix is not symmetric")

        if not np.allclose(np.diag(self.data), 1.0):
            raise ValueError("correlation diagonal should be filled with 1")

        return self

    @staticmethod
    def from_hydro_correlations(correlations: dict[str, HydroCorrelation]) -> "HydroCorrelationMatrix":
        area_ids = sorted(correlations)
        array = np.identity(len(correlations))

        for area_id, corr in correlations.items():
            for correlation in corr.correlation:
                i = area_ids.index(area_id)
                j = area_ids.index(correlation.area_id)
                array[i][j] = array[j][i] = correlation.coefficient / 100

        return HydroCorrelationMatrix.model_validate({"index": area_ids, "columns": area_ids, "data": array})

    def set_correlation(self, area_id: str, data: HydroCorrelation) -> None:
        index = self.index.index(area_id)
        modified_indexes = {index}
        for correlation in data.correlation:
            other_index = self.index.index(correlation.area_id)
            self.data[index][other_index] = self.data[other_index][index] = correlation.coefficient / 100
            modified_indexes.add(other_index)

        # Reset existing values that were not modified
        for other_index in range(len(self.index)):
            if other_index not in modified_indexes:
                self.data[index][other_index] = self.data[other_index][index] = 0

        # Validate the data we modified
        self._validate_model()

    def to_hydro_correlations(self) -> dict[str, HydroCorrelation]:
        correlations_dict = {}
        for k, area_id in enumerate(self.index):
            correlations = [
                HydroCorrelationArea(area_id=self.index[m], coefficient=n * 100) for m, n in enumerate(self.data[k])
            ]
            correlations_dict[area_id] = HydroCorrelation(correlation=correlations)
        return correlations_dict
