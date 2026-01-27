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
from typing import Any

import pandas as pd
from pydantic import Field, model_validator
from pydantic.alias_generators import to_camel

from antarest.core.serde import AntaresBaseModel
from antarest.core.serde.np_array import NpArray


class HydroAllocationArea(AntaresBaseModel, extra="forbid", populate_by_name=True, alias_generator=to_camel):
    area_id: str
    coefficient: float = Field(allow_inf_nan=False)


class HydroAllocation(AntaresBaseModel, extra="forbid", populate_by_name=True):
    allocation: list[HydroAllocationArea]

    @model_validator(mode="after")
    def check_allocation(self) -> "HydroAllocation":
        allocation = self.allocation

        if not allocation:
            raise ValueError("allocation must not be empty")

        if len(allocation) != len({a.area_id for a in allocation}):
            raise ValueError("allocation must not contain duplicate area IDs")

        if all(a.coefficient == 0 for a in allocation):
            raise ValueError("at least one allocation coefficient must be non-zero")

        if sum(a.coefficient for a in allocation) <= 0:
            raise ValueError("sum of coefficients must be positive")

        return self


class HydroAllocationMatrix(AntaresBaseModel, extra="forbid", populate_by_name=True, arbitrary_types_allowed=True):
    """
    Hydraulic allocation matrix.
    index: List of all study areas
    columns: List of selected production areas
    data: 2D-array matrix of consumption coefficients
    """

    index: list[str]
    columns: list[str]
    data: NpArray

    @staticmethod
    def from_hydro_allocations(allocations: dict[str, HydroAllocation]) -> "HydroAllocationMatrix":
        if not allocations:
            raise ValueError("allocation matrix must not be empty")

        df_args: dict[str, Any] = {}
        for area_id, allocation_list in allocations.items():
            df_args[area_id] = {}
            for allocation in allocation_list.allocation:
                df_args[area_id][allocation.area_id] = allocation.coefficient

        df = pd.DataFrame.from_dict(df_args)
        args: dict[str, Any] = {"data": df.reindex(df.columns).transpose().fillna(0).to_numpy()}
        args["index"] = args["columns"] = list(df.columns)
        return HydroAllocationMatrix.model_validate(args)
