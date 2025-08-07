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
from antarest.study.business.model.hydro_model import (
    HydroManagement,
    InflowStructure,
    initialize_hydro_management,
    initialize_inflow_structure,
    validate_hydro_management_against_version,
)


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

    def to_model(self, area_id: str) -> HydroManagement:
        lower_area_id = area_id.lower()
        data = self.model_dump(mode="json").items()

        args = {key: values.get(lower_area_id) for key, values in data if values and lower_area_id in values}
        return HydroManagement.model_validate(args)

    @classmethod
    def from_model(
        cls,
        hydro_management: HydroManagement,
        area_id: str,
    ) -> "HydroManagementFileData":
        lower_area_id = area_id.lower()
        hydro_data = hydro_management.model_dump(exclude_none=True)
        args: dict[str, Any] = {}
        for key, value in hydro_data.items():
            args.setdefault(key, {})[lower_area_id] = value
        return HydroManagementFileData.model_validate(args)


class InflowStructureFileData(AntaresBaseModel, extra="forbid", populate_by_name=True):
    inter_monthly_correlation: Optional[float] = Field(
        default=None,
        ge=0,
        le=1,
        alias="intermonthly-correlation",
    )

    def to_model(self) -> InflowStructure:
        return InflowStructure.model_validate(self.model_dump(exclude_none=True))

    @classmethod
    def from_model(cls, inflow_structure: InflowStructure) -> "InflowStructureFileData":
        return cls.model_validate(inflow_structure.model_dump(exclude={"id"}))


def parse_hydro_management(area_id: str, file_data: dict[str, Any], study_version: StudyVersion) -> HydroManagement:
    hydro_management = HydroManagementFileData.model_validate(file_data).to_model(area_id)
    validate_hydro_management_against_version(study_version, hydro_management)
    initialize_hydro_management(hydro_management, study_version)
    return hydro_management


def parse_inflow_structure(file_data: dict[str, Any]) -> InflowStructure:
    inflow_structure = InflowStructureFileData.model_validate(file_data).to_model()
    initialize_inflow_structure(inflow_structure)
    return inflow_structure


def serialize_hydro_management(
    hydro_management: HydroManagement, area_id: str, study_version: StudyVersion
) -> dict[str, Any]:
    validate_hydro_management_against_version(study_version, hydro_management)
    return HydroManagementFileData.from_model(hydro_management, area_id).model_dump(
        mode="json", exclude_none=True, by_alias=True
    )


def serialize_inflow_structure(inflow_structure: InflowStructure) -> dict[str, Any]:
    return InflowStructureFileData.from_model(inflow_structure).model_dump(exclude_none=True, by_alias=True)
