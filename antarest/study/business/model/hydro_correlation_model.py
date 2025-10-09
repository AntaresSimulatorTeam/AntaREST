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

import numpy as np
from pydantic import Field, model_validator
from pydantic.alias_generators import to_camel

from antarest.core.serde import AntaresBaseModel
from antarest.core.serde.np_array import NpArray


class HydroCorrelationArea(AntaresBaseModel, extra="forbid", populate_by_name=True, alias_generator=to_camel):
    area_id: str
    coefficient: float = Field(allow_inf_nan=False, gt=-100, lt=100)


class HydroCorrelation(AntaresBaseModel, extra="forbid", populate_by_name=True):
    correlation: list[HydroCorrelationArea]

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
        if self.data.size == 0:
            raise ValueError("correlation matrix must not be empty")

        if self.index != self.columns:
            raise ValueError("correlation matrix must have the same rows and columns")

        if np.any((self.data < -1) | np.any(self.data > 1)):
            raise ValueError("coefficients must be between -1 and 1")

        if np.any(np.isnan(self.data)):
            raise ValueError("correlation matrix must not contain NaN coefficients")

        n = len(self.index)
        if self.data.shape != (n, n):
            raise ValueError(f"correlation matrix must have shape ({n}×{n})")

        if not np.array_equal(self.data, self.data.T):
            raise ValueError("correlation matrix is not symmetric")

        if np.any(np.diag(self.data) != 1):
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
                array[i][j] = correlation.coefficient
                array[j][i] = correlation.coefficient

        return HydroCorrelationMatrix.model_validate({"index": area_ids, "columns": area_ids, "data": array})

    def to_hydro_correlations(self) -> dict[str, HydroCorrelation]:
        correlations_dict = {}
        for k, area_id in enumerate(self.index):
            correlations = [HydroCorrelationArea(area_id=self.index[k], coefficient=n) for n in self.data[k]]
            correlations_dict[area_id] = HydroCorrelation(correlation=correlations)
        return correlations_dict
