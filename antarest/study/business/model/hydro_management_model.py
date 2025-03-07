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

from pydantic import AliasChoices, Field

from antarest.core.serde import AntaresBaseModel
from antarest.core.utils.string import to_camel_case

INFLOW_PATH = "input/hydro/prepro/{area_id}/prepro/prepro"
HYDRO_PATH = ["input", "hydro", "hydro"]


class InflowStructure(
    AntaresBaseModel, extra="forbid", validate_assignment=True, populate_by_name=True, alias_generator=to_camel_case
):
    """Represents the inflow structure values in the hydraulic configuration."""

    # NOTE: Currently, there is only one field for the inflow structure model
    # due to the scope of hydro config requirements, it may change.
    inter_monthly_correlation: float = Field(
        default=0.5,
        ge=0,
        le=1,
        description="Average correlation between the energy of a month and that of the next month",
        title="Inter-monthly correlation",
    )


class HydroManagementOptions(
    AntaresBaseModel, extra="forbid", validate_assignment=True, populate_by_name=True, alias_generator=to_camel_case
):
    inter_daily_breakdown: Optional[float] = Field(
        default=1, ge=0, validation_alias=AliasChoices("interDailyBreakdown", "inter-daily-breakdown")
    )
    intra_daily_modulation: Optional[float] = Field(
        default=24, ge=1, validation_alias=AliasChoices("intraDailyModulation", "intra-daily-modulation")
    )
    inter_monthly_breakdown: Optional[float] = Field(
        default=1, ge=0, validation_alias=AliasChoices("interMonthlyBreakdown", "inter-monthly-breakdown")
    )
    reservoir: Optional[bool] = False
    reservoir_capacity: Optional[float] = Field(
        default=0, ge=0, validation_alias=AliasChoices("reservoirCapacity", "reservoir capacity")
    )
    follow_load: Optional[bool] = Field(default=True, validation_alias=AliasChoices("followLoad", "follow load"))
    use_water: Optional[bool] = Field(default=False, validation_alias=AliasChoices("useWater", "use water"))
    hard_bounds: Optional[bool] = Field(default=False, validation_alias=AliasChoices("hardBounds", "hard bounds"))
    initialize_reservoir_date: Optional[int] = Field(
        default=0, ge=0, le=11, validation_alias=AliasChoices("initializeReservoirDate", "initialize reservoir date")
    )
    use_heuristic: Optional[bool] = Field(default=True, validation_alias=AliasChoices("useHeuristic", "use heuristic"))
    power_to_level: Optional[bool] = Field(
        default=False, validation_alias=AliasChoices("powerToLevel", "power to level")
    )
    use_leeway: Optional[bool] = Field(default=False, validation_alias=AliasChoices("useLeeway", "use leeway"))
    leeway_low: Optional[float] = Field(default=1, ge=0, validation_alias=AliasChoices("leewayLow", "leeway low"))
    leeway_up: Optional[float] = Field(default=1, ge=0, validation_alias=AliasChoices("leewayUp", "leeway up"))
    pumping_efficiency: Optional[float] = Field(
        default=1, ge=0, validation_alias=AliasChoices("pumpingEfficiency", "pumping efficiency")
    )


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
