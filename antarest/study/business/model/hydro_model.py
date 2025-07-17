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
from typing import Any, Optional

from antares.study.version import StudyVersion
from pydantic import Field
from pydantic.alias_generators import to_camel

from antarest.core.model import LowerCaseStr
from antarest.core.serde import AntaresBaseModel
from antarest.study.model import STUDY_VERSION_9_2

HYDRO_PATH = ["input", "hydro", "hydro"]


def get_inflow_path(area_id: str) -> list[str]:
    return ["input", "hydro", "prepro", area_id, "prepro", "prepro"]


class HydroManagement(AntaresBaseModel, extra="forbid", populate_by_name=True, alias_generator=to_camel):
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
    # v9.2 field
    overflow_spilled_cost_difference: Optional[float] = None


class HydroManagementUpdate(AntaresBaseModel, extra="forbid", populate_by_name=True, alias_generator=to_camel):
    inter_daily_breakdown: Optional[float] = Field(default=None, ge=0)
    intra_daily_modulation: Optional[float] = Field(default=None, ge=1)
    inter_monthly_breakdown: Optional[float] = Field(default=None, ge=0)
    reservoir: Optional[bool] = None
    reservoir_capacity: Optional[float] = Field(default=None, ge=0)
    follow_load: Optional[bool] = None
    use_water: Optional[bool] = None
    hard_bounds: Optional[bool] = None
    initialize_reservoir_date: Optional[int] = Field(default=None, ge=0, le=11)
    use_heuristic: Optional[bool] = None
    power_to_level: Optional[bool] = None
    use_leeway: Optional[bool] = None
    leeway_low: Optional[float] = Field(default=None, ge=0)
    leeway_up: Optional[float] = Field(default=None, ge=0)
    pumping_efficiency: Optional[float] = Field(default=None, ge=0)
    # v9.2 field
    overflow_spilled_cost_difference: Optional[float] = None

    def validate_model_against_version(self, study_version: StudyVersion) -> None:
        if study_version < STUDY_VERSION_9_2 and self.overflow_spilled_cost_difference is not None:
            raise ValueError("You cannot fill the parameter `overflow_spilled_cost_difference` before the v9.2")


class HydroManagementFileData(AntaresBaseModel, extra="forbid", populate_by_name=True):
    inter_daily_breakdown: Optional[dict[LowerCaseStr, float]] = Field(default=None, alias="inter-daily-breakdown")
    intra_daily_modulation: Optional[dict[LowerCaseStr, float]] = Field(default=None, alias="intra-daily-modulation")
    inter_monthly_breakdown: Optional[dict[LowerCaseStr, float]] = Field(default=None, alias="inter-monthly-breakdown")
    reservoir: Optional[dict[LowerCaseStr, bool]] = None
    reservoir_capacity: Optional[dict[LowerCaseStr, float]] = Field(default=None, alias="reservoir capacity")
    follow_load: Optional[dict[LowerCaseStr, bool]] = Field(default=None, alias="follow load")
    use_water: Optional[dict[LowerCaseStr, bool]] = Field(default=None, alias="use water")
    hard_bounds: Optional[dict[LowerCaseStr, bool]] = Field(default=None, alias="hard bounds")
    initialize_reservoir_date: Optional[dict[LowerCaseStr, int]] = Field(
        default=None, alias="initialize reservoir date"
    )
    use_heuristic: Optional[dict[LowerCaseStr, bool]] = Field(default=None, alias="use heuristic")
    power_to_level: Optional[dict[LowerCaseStr, bool]] = Field(default=None, alias="power to level")
    use_leeway: Optional[dict[LowerCaseStr, float]] = Field(default=None, alias="use leeway")
    leeway_low: Optional[dict[LowerCaseStr, float]] = Field(default=None, alias="leeway low")
    leeway_up: Optional[dict[LowerCaseStr, float]] = Field(default=None, alias="leeway up")
    pumping_efficiency: Optional[dict[LowerCaseStr, float]] = Field(default=None, alias="pumping efficiency")
    # v9.2 field
    overflow_spilled_cost_difference: Optional[dict[LowerCaseStr, float]] = Field(
        default=None, alias="overflow spilled cost difference"
    )

    def get_hydro_management(self, area_id: str, study_version: StudyVersion) -> HydroManagement:
        excludes = self._get_fields_to_exclude(study_version)

        lower_area_id = area_id.lower()
        args = {
            key: values.get(lower_area_id)
            for key, values in self.model_dump(mode="json", exclude=excludes).items()
            if values and lower_area_id in values
        }
        args = self._add_default_values(args, study_version)
        return HydroManagement(**args)

    @staticmethod
    def _get_fields_to_exclude(study_version: StudyVersion) -> set[str]:
        excludes = set()
        if study_version < STUDY_VERSION_9_2:
            excludes.add("overflow_spilled_cost_difference")
        return excludes

    @staticmethod
    def _add_default_values(data: dict[str, Any], study_version: StudyVersion) -> dict[str, Any]:
        if study_version >= STUDY_VERSION_9_2 and "overflow_spilled_cost_difference" not in data:
            data["overflow_spilled_cost_difference"] = 1
        return data

    def set_hydro_management(self, area_id: str, properties: HydroManagement) -> None:
        lower_area_id = area_id.lower()
        properties_dict = properties.model_dump(exclude_none=True)

        for prop_key, prop_value in properties_dict.items():
            current_dict = getattr(self, prop_key, {})
            if current_dict is None:
                current_dict = {}

            current_dict[lower_area_id] = prop_value

            setattr(self, prop_key, current_dict)


class InflowStructure(AntaresBaseModel, extra="forbid", populate_by_name=True, alias_generator=to_camel):
    """Represents the inflow structure in the hydraulic configuration."""

    inter_monthly_correlation: float = Field(
        default=0.5,
        ge=0,
        le=1,
        description="Average correlation between the energy of a month and that of the next month",
        title="Inter-monthly correlation",
    )


class InflowStructureUpdate(AntaresBaseModel, extra="forbid", populate_by_name=True, alias_generator=to_camel):
    inter_monthly_correlation: Optional[float] = Field(
        default=None,
        ge=0,
        le=1,
        description="Average correlation between the energy of a month and that of the next month",
        title="Inter-monthly correlation",
    )


class InflowStructureFileData(AntaresBaseModel, extra="forbid", populate_by_name=True):
    inter_monthly_correlation: Optional[float] = Field(
        default=None,
        ge=0,
        le=1,
        alias="intermonthly-correlation",
    )


class HydroProperties(AntaresBaseModel, extra="forbid", populate_by_name=True, alias_generator=to_camel):
    management_options: HydroManagement
    inflow_structure: InflowStructure


def update_hydro_management(hydro_management: HydroManagement, hydro_data: HydroManagementUpdate) -> HydroManagement:
    return hydro_management.model_copy(update=hydro_data.model_dump(exclude_none=True))


def update_inflow_structure(
    inflow_structure: InflowStructureFileData, inflow_data: InflowStructureUpdate
) -> InflowStructureFileData:
    return inflow_structure.model_copy(update=inflow_data.model_dump(exclude_none=True))
