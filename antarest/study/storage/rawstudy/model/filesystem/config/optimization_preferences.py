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
from antarest.study.business.model.config.optimization_config import LegacyTransmissionCapacities, \
    TransmissionCapacities, UnfeasibleProblemBehavior, SimplexOptimizationRange


class OptimizationPreferencesFileData(AntaresBaseModel):
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