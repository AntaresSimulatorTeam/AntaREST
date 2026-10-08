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
from antares.study.version import StudyVersion
from pydantic import ConfigDict
from pydantic.alias_generators import to_camel

from antarest.core.exceptions import InvalidFieldForVersionError
from antarest.core.serde import AntaresBaseModel
from antarest.study.business.enum_ignore_case import EnumIgnoreCase
from antarest.study.model import STUDY_VERSION_10_2, STUDY_VERSION_10_3


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


class ExportMPS(EnumIgnoreCase):
    """Allow to export the optimization problem in MPS format.

    Before study version 8.3 only boolean values were allowed.
    Since 8.3, these values are allowed in addition to boolean ones:
    `True` is equivalent to `BOTH_OPTIMS` and `False` is equivalent to `NONE`.
    """

    NONE = "none"
    OPTIM1 = "optim-1"
    OPTIM2 = "optim-2"
    BOTH_OPTIMS = "both-optims"


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
    export_mps: bool | ExportMPS = False
    unfeasible_problem_behavior: UnfeasibleProblemBehavior = UnfeasibleProblemBehavior.ERROR_VERBOSE
    simplex_optimization_range: SimplexOptimizationRange = SimplexOptimizationRange.WEEK
    # Since v10.2
    include_reserves: bool | None = None
    # Since v10.3
    include_thermal_cluster_ramping: bool | None = None


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
    export_mps: bool | ExportMPS | None = None
    unfeasible_problem_behavior: UnfeasibleProblemBehavior | None = None
    simplex_optimization_range: SimplexOptimizationRange | None = None
    include_reserves: bool | None = None
    include_thermal_cluster_ramping: bool | None = None


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


def initialize_optimization_preferences_against_version(
    parameters: OptimizationPreferences, version: StudyVersion
) -> None:
    if version >= STUDY_VERSION_10_2 and parameters.include_reserves is None:
        parameters.include_reserves = False
    if version >= STUDY_VERSION_10_3 and parameters.include_thermal_cluster_ramping is None:
        parameters.include_thermal_cluster_ramping = False


def validate_optimization_preferences_against_version(
    version: StudyVersion, parameters: OptimizationPreferences | OptimizationPreferencesUpdate
) -> None:
    for field, min_version in (
        ("include_reserves", STUDY_VERSION_10_2),
        ("include_thermal_cluster_ramping", STUDY_VERSION_10_3),
    ):
        if version < min_version and getattr(parameters, field) is not None:
            raise InvalidFieldForVersionError(
                f"Field {field} is not a valid field for study version before {min_version:2d}"
            )
