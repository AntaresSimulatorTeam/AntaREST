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

from antarest.core.model import LowerCaseStr
from antarest.core.serde import AntaresBaseModel
from antarest.study.business.model.hydro_model import HydroManagement, InflowStructure
from antarest.study.model import STUDY_VERSION_9_2


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


class InflowStructureFileData(AntaresBaseModel, extra="forbid", populate_by_name=True):
    inter_monthly_correlation: Optional[float] = Field(
        default=None,
        ge=0,
        le=1,
        alias="intermonthly-correlation",
    )


def parse_hydro_management(
    hydro_file_data: HydroManagementFileData, area_id: str, study_version: StudyVersion
) -> HydroManagement:
    return hydro_file_data.get_hydro_management(area_id, study_version)


def parse_inflow_structure(data: Any) -> InflowStructure:
    inflow_data = InflowStructureFileData.model_validate(data)
    return InflowStructure(**inflow_data.model_dump())


def serialize_hydro_management(hydro_management: HydroManagement) -> dict[str, Any]:
    return hydro_management.model_dump()


def serialize_inflow_structure(inflow_structure: InflowStructure) -> dict[str, Any]:
    return inflow_structure.model_dump()


def get_hydro_management_file_data(file_data: dict[str, Any]) -> HydroManagementFileData:
    return HydroManagementFileData.model_construct(**file_data)


def get_inflow_structure_file_data(inflow_structure: InflowStructure) -> InflowStructureFileData:
    return InflowStructureFileData.model_validate(**serialize_inflow_structure(inflow_structure))
