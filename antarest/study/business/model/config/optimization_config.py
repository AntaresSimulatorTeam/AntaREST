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
from pydantic import ConfigDict
from pydantic.alias_generators import to_camel

from antarest.core.serde import AntaresBaseModel
from antarest.study.business.enum_ignore_case import EnumIgnoreCase

OPTIMIZATION_PATH = ["settings", "generaldata", "optimization"]


class LegacyTransmissionCapacities(EnumIgnoreCase):
    INFINITE = "infinite"


class TransmissionCapacities(EnumIgnoreCase):
    LOCAL_VALUES = "local-values"
    NULL_FOR_ALL_LINKS = "null-for-all-links"
    INFINITE_FOR_ALL_LINKS = "infinite-for-all-links"
    NULL_FOR_PHYSICAL_LINKS = "null-for-physical-links"
    INFINITE_FOR_PHYSICAL_LINKS = "infinite-for-physical-links"


class UnfeasibleProblemBehavior(EnumIgnoreCase):
    WARNING_DRY = "warning-dry"
    WARNING_VERBOSE = "warning-verbose"
    ERROR_DRY = "error-dry"
    ERROR_VERBOSE = "error-verbose"


class SimplexOptimizationRange(EnumIgnoreCase):
    DAY = "day"
    WEEK = "week"


class OptimizationPreferences(AntaresBaseModel):
    model_config = ConfigDict(alias_generator=to_camel, extra="forbid", populate_by_name=True)

    binding_constraints: bool = True
    hurdle_costs: bool = True
    transmission_capacities: bool | LegacyTransmissionCapacities | TransmissionCapacities = True
    thermal_clusters_min_stable_power: bool = True
    thermal_clusters_min_ud_time: bool = True
    day_ahead_reserve: bool = True
    primary_reserve: bool = True
    strategic_reserve: bool = True
    spinning_reserve: bool = True
    export_mps: bool | str = False
    unfeasible_problem_behavior: UnfeasibleProblemBehavior = UnfeasibleProblemBehavior.ERROR_VERBOSE
    simplex_optimization_range: SimplexOptimizationRange = SimplexOptimizationRange.WEEK


class OptimizationPreferencesUpdate(AntaresBaseModel):
    model_config = ConfigDict(alias_generator=to_camel, extra="forbid", populate_by_name=True)

    binding_constraints: bool | None = None
    hurdle_costs: bool | None = None
    transmission_capacities: bool | LegacyTransmissionCapacities | TransmissionCapacities | None = None
    thermal_clusters_min_stable_power: bool | None = None
    thermal_clusters_min_ud_time: bool | None = None
    day_ahead_reserve: bool | None = None
    primary_reserve: bool | None = None
    strategic_reserve: bool | None = None
    spinning_reserve: bool | None = None
    export_mps: bool | str | None = None
    unfeasible_problem_behavior: UnfeasibleProblemBehavior | None = None
    simplex_optimization_range: SimplexOptimizationRange | None = None


def update_optimization_preferences(
    config: OptimizationPreferences, new_config: OptimizationPreferencesUpdate
) -> OptimizationPreferences:
    """
    Updates the optimization preferences according to the provided update data.
    """
    current_properties = config.model_dump(mode="json")
    new_properties = new_config.model_dump(mode="json", exclude_none=True)
    current_properties.update(new_properties)
    return OptimizationPreferences.model_validate(current_properties)
