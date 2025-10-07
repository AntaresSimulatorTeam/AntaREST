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
from annotated_types import Len
from pydantic import Field, model_validator
from pydantic.alias_generators import to_camel
from typing_extensions import Annotated

from antarest.core.serde import AntaresBaseModel
from antarest.core.serde.np_array import NpArray


class HydroAllocationArea(AntaresBaseModel, extra="forbid", populate_by_name=True, alias_generator=to_camel):
    area_id: str
    coefficient: float = Field(allow_inf_nan=False)


class HydroAllocation(AntaresBaseModel, extra="forbid", populate_by_name=True):
    allocations: list[HydroAllocationArea]

    @model_validator(mode="after")
    def check_allocation(self) -> "HydroAllocation":
        allocation = self.allocations

        if not allocation:
            raise ValueError("allocation must not be empty")

        if len(allocation) != len({a.area_id for a in allocation}):
            raise ValueError("allocation must not contain duplicate area IDs")

        if all(a.coefficient == 0 for a in allocation):
            raise ValueError("at least one allocation coefficient must be non-zero")

        if sum(a.coefficient for a in allocation) <= 0:
            raise ValueError("sum of coefficients must be positive")

        return self


class AllocationMatrix(AntaresBaseModel, extra="forbid", populate_by_name=True, arbitrary_types_allowed=True):
    """
    Hydraulic allocation matrix.
    index: List of all study areas
    columns: List of selected production areas
    data: 2D-array matrix of consumption coefficients
    """

    index: Annotated[list[str], Len(min_length=1)]
    columns: Annotated[list[str], Len(min_length=1)]
    data: NpArray

    @model_validator(mode="after")
    def check_coherence(self) -> "AllocationMatrix":
        if self.data.size == 0:
            raise ValueError("allocation matrix must not be empty")

        if self.data.shape != (len(self.index), len(self.columns)):
            raise ValueError("allocation matrix shape is inconsistent")

        if self.index != self.columns:
            raise ValueError("allocation matrix index and columns should be the same")

        return self

    def to_hydro_allocations(self) -> dict[str, HydroAllocation]:
        allocations_dict = {}
        N = len(self.index)
        for k in range(N):
            allocations = []
            for n in range(N):
                coefficient = self.data[k][n]
                if coefficient != 0:
                    allocations.append(HydroAllocationArea(area_id=self.index[n], coefficient=coefficient))
            allocations_dict[self.index[k]] = HydroAllocation(allocations=allocations)
        return allocations_dict

    @staticmethod
    def from_hydro_allocations(allocations: dict[str, HydroAllocation]) -> "AllocationMatrix":
        raise NotImplementedError()
