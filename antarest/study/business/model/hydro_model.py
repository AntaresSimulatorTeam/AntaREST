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
from typing import Dict, Optional

from pydantic import Field

from antarest.core.model import LowerCaseStr
from antarest.core.serde import AntaresBaseModel
from antarest.core.utils.string import to_camel_case
from antarest.study.business.all_optional_meta import all_optional_model, camel_case_model

HYDRO_PATH = ["input", "hydro", "hydro"]


class HydroManagement(AntaresBaseModel, extra="forbid", populate_by_name=True, alias_generator=to_camel_case):
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


@all_optional_model
@camel_case_model
class HydroManagementUpdate(AntaresBaseModel, extra="forbid", populate_by_name=True):
    inter_daily_breakdown: float = Field(ge=0)
    intra_daily_modulation: float = Field(ge=1)
    inter_monthly_breakdown: float = Field(ge=0)
    reservoir: bool
    reservoir_capacity: float = Field(ge=0)
    follow_load: bool
    use_water: bool
    hard_bounds: bool
    initialize_reservoir_date: int = Field(ge=0, le=11)
    use_heuristic: bool
    power_to_level: bool
    use_leeway: bool
    leeway_low: float = Field(ge=0)
    leeway_up: float = Field(ge=0)
    pumping_efficiency: float = Field(ge=0)


@all_optional_model
class HydroManagementProperties(AntaresBaseModel, extra="forbid", populate_by_name=True):
    inter_daily_breakdown: Dict[LowerCaseStr, float] = Field(alias="inter-daily-breakdown")
    intra_daily_modulation: Dict[LowerCaseStr, float] = Field(alias="intra-daily-modulation")
    inter_monthly_breakdown: Dict[LowerCaseStr, float] = Field(alias="inter-monthly-breakdown")
    reservoir: Dict[LowerCaseStr, bool]
    reservoir_capacity: Dict[LowerCaseStr, float] = Field(alias="reservoir capacity")
    follow_load: Dict[LowerCaseStr, bool] = Field(alias="follow load")
    use_water: Dict[LowerCaseStr, bool] = Field(alias="use water")
    hard_bounds: Dict[LowerCaseStr, bool] = Field(alias="hard bounds")
    initialize_reservoir_date: Dict[LowerCaseStr, int] = Field(alias="initialize reservoir date")
    use_heuristic: Dict[LowerCaseStr, bool] = Field(alias="use heuristic")
    power_to_level: Dict[LowerCaseStr, bool] = Field(alias="power to level")
    use_leeway: Dict[LowerCaseStr, float] = Field(alias="use leeway")
    leeway_low: Dict[LowerCaseStr, float] = Field(alias="leeway low")
    leeway_up: Dict[LowerCaseStr, float] = Field(alias="leeway up")
    pumping_efficiency: Dict[LowerCaseStr, float] = Field(alias="pumping efficiency")

    def get_hydro_management(self, area_id: str) -> HydroManagement:
        lower_area_id = area_id.lower()
        args = {
            key: values.get(lower_area_id)
            for key, values in self.model_dump().items()
            if values and lower_area_id in values
        }
        return HydroManagement(**args)

    def set_hydro_management(self, area_id: str, properties: HydroManagement) -> None:
        lower_area_id = area_id.lower()
        properties_dict = properties.model_dump(exclude_none=True)

        for prop_key, prop_value in properties_dict.items():
            current_dict = getattr(self, prop_key, {})
            if current_dict is None:
                current_dict = {}

            current_dict[lower_area_id] = prop_value

            setattr(self, prop_key, current_dict)
