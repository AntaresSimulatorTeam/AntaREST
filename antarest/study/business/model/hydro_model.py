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
from typing import Any, Dict, Optional

from pydantic import Field

from antarest.core.serde import AntaresBaseModel
from antarest.core.utils.string import to_camel_case

HYDRO_PATH = ["input", "hydro", "hydro"]


class HydroProperties(AntaresBaseModel, extra="forbid", populate_by_name=True, alias_generator=to_camel_case):
    inter_daily_breakdown: Optional[float] = Field(default=1, ge=0)
    intra_daily_modulation: Optional[float] = Field(default=24, ge=1)
    inter_monthly_breakdown: Optional[float] = Field(default=1, ge=0)
    reservoir: Optional[bool] = False
    reservoir_capacity: Optional[float] = Field(default=0, ge=0)
    follow_load: Optional[bool] = Field(default=True)
    use_water: Optional[bool] = Field(default=False)
    hard_bounds: Optional[bool] = Field(default=False)
    initialize_reservoir_date: Optional[int] = Field(default=0, ge=0, le=11)
    use_heuristic: Optional[bool] = Field(default=True)
    power_to_level: Optional[bool] = Field(default=False)
    use_leeway: Optional[bool] = Field(default=False)
    leeway_low: Optional[float] = Field(default=1, ge=0)
    leeway_up: Optional[float] = Field(default=1, ge=0)
    pumping_efficiency: Optional[float] = Field(default=1, ge=0)


class HydroPropertiesInternal(AntaresBaseModel, extra="forbid", populate_by_name=True):
    inter_daily_breakdown: Optional[float] = Field(default=1, ge=0, alias="inter-daily-breakdown")
    intra_daily_modulation: Optional[float] = Field(default=24, ge=1, alias="intra-daily-modulation")
    inter_monthly_breakdown: Optional[float] = Field(default=1, ge=0, alias="inter-monthly-breakdown")
    reservoir: Optional[bool] = False
    reservoir_capacity: Optional[float] = Field(default=0, ge=0, alias="reservoir capacity")
    follow_load: Optional[bool] = Field(default=True, alias="follow load")
    use_water: Optional[bool] = Field(default=False, alias="use water")
    hard_bounds: Optional[bool] = Field(default=False, alias="hard bounds")
    initialize_reservoir_date: Optional[int] = Field(default=0, ge=0, le=11, alias="initialize reservoir date")
    use_heuristic: Optional[bool] = Field(default=True, alias="use heuristic")
    power_to_level: Optional[bool] = Field(default=False, alias="power to level")
    use_leeway: Optional[bool] = Field(default=False, alias="use leeway")
    leeway_low: Optional[float] = Field(default=1, ge=0, alias="leeway low")
    leeway_up: Optional[float] = Field(default=1, ge=0, alias="leeway up")
    pumping_efficiency: Optional[float] = Field(default=1, ge=0, alias="pumping efficiency")


def get_hydro_id(area_id: str, field_dict: Dict[str, Any]) -> str:
    """
    Try to match the current area_id with the one from the original file.
    These two ids could mismatch based on their character cases since the id from
    the filesystem could have been modified with capital letters.
    We first convert it into lower case in order to compare both ids.

    Returns the area id from the file if both values matched, the initial area id otherwise.
    """
    return next(
        (key for sub_dict in field_dict.values() for key in sub_dict if key.lower() == area_id.lower()), area_id
    )
