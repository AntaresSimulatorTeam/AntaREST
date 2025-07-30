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
from typing import Any, Dict

from pydantic import ConfigDict, Field

from antarest.core.serde import AntaresBaseModel
from antarest.study.business.model.config.optimization_config import (
    LegacyTransmissionCapacities,
    OptimizationPreferences,
    SimplexOptimizationRange,
    TransmissionCapacities,
    UnfeasibleProblemBehavior,
)


class OptimizationPreferencesFileData(AntaresBaseModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    binding_constraints: bool | None = Field(default=None, alias="include-constraints")
    hurdle_costs: bool | None = Field(default=None, alias="include-hurdlecosts")
    transmission_capacities: bool | LegacyTransmissionCapacities | TransmissionCapacities | None = Field(
        default=None, alias="transmission-capacities"
    )
    thermal_clusters_min_stable_power: bool | None = Field(default=None, alias="include-tc-minstablepower")
    thermal_clusters_min_ud_time: bool | None = Field(default=None, alias="include-tc-min-ud-time")
    day_ahead_reserve: bool | None = Field(default=None, alias="include-dayahead")
    primary_reserve: bool | None = Field(default=None, alias="include-primaryreserve")
    strategic_reserve: bool | None = Field(default=None, alias="include-strategicreserve")
    spinning_reserve: bool | None = Field(default=None, alias="include-spinningreserve")
    export_mps: bool | str | None = Field(default=None, alias="include-exportmps")
    unfeasible_problem_behavior: UnfeasibleProblemBehavior | None = Field(
        default=None, alias="include-unfeasible-problem-behavior"
    )
    simplex_optimization_range: SimplexOptimizationRange | None = Field(default=None, alias="simplex-range")

    def to_model(self) -> OptimizationPreferences:
        return OptimizationPreferences.model_validate(self.model_dump(exclude_none=True))

    @classmethod
    def from_model(cls, config: OptimizationPreferences) -> "OptimizationPreferencesFileData":
        return cls.model_validate(config.model_dump())


def parse_optimization_preferences(data: Dict[str, Any]) -> OptimizationPreferences:
    return OptimizationPreferencesFileData.model_validate(data).to_model()


def serialize_optimization_preferences(config: OptimizationPreferences) -> dict[str, Any]:
    return OptimizationPreferencesFileData.from_model(config).model_dump(mode="json", by_alias=True, exclude_none=True)
