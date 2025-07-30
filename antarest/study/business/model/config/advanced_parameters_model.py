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
from typing import Annotated, Any, Optional, TypeAlias

from antares.study.version import StudyVersion
from pydantic import BeforeValidator, ConfigDict
from pydantic.alias_generators import to_camel

from antarest.core.exceptions import InvalidFieldForVersionError
from antarest.core.serde import AntaresBaseModel
from antarest.study.business.enum_ignore_case import EnumIgnoreCase
from antarest.study.model import STUDY_VERSION_8_8, STUDY_VERSION_9_2, STUDY_VERSION_9_3


class InitialReservoirLevel(EnumIgnoreCase):
    COLD_START = "cold start"
    HOT_START = "hot start"


class HydroHeuristicPolicy(EnumIgnoreCase):
    ACCOMMODATE_RULES_CURVES = "accommodate rule curves"
    MAXIMIZE_GENERATION = "maximize generation"


class HydroPricingMode(EnumIgnoreCase):
    FAST = "fast"
    ACCURATE = "accurate"


class PowerFluctuation(EnumIgnoreCase):
    FREE_MODULATIONS = "free modulations"
    MINIMIZE_EXCURSIONS = "minimize excursions"
    MINIMIZE_RAMPING = "minimize ramping"


class SheddingPolicy(EnumIgnoreCase):
    SHAVE_PEAKS = "shave peaks"
    ACCURATE_SHAVE_PEAKS = "accurate shave peaks"
    MINIMIZE_DURATION = "minimize duration"


class ReserveManagement(EnumIgnoreCase):
    GLOBAL = "global"


class UnitCommitmentMode(EnumIgnoreCase):
    FAST = "fast"
    ACCURATE = "accurate"
    MILP = "milp"


class SimulationCore(EnumIgnoreCase):
    MINIMUM = "minimum"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    MAXIMUM = "maximum"


class RenewableGenerationModeling(EnumIgnoreCase):
    AGGREGATED = "aggregated"
    CLUSTERS = "clusters"


def _validate_accuracy_on_correlation(v: str) -> str:
    sanitized_v = v.strip().replace(" ", "")
    if not sanitized_v:
        return ""

    values_list = sanitized_v.split(",")
    if len(values_list) != len(set(values_list)):
        raise ValueError("Duplicate value")

    allowed_values = ["wind", "load", "solar"]
    for value in values_list:
        if value not in allowed_values:
            raise ValueError(f"Invalid value: {value}")

    return v


AccuracyOnCorrelation: TypeAlias = Annotated[str, BeforeValidator(_validate_accuracy_on_correlation)]


class AdvancedParameters(AntaresBaseModel):
    model_config = ConfigDict(alias_generator=to_camel, extra="forbid", populate_by_name=True)

    accuracy_on_correlation: AccuracyOnCorrelation = ""
    power_fluctuations: PowerFluctuation = PowerFluctuation.FREE_MODULATIONS
    shedding_policy: SheddingPolicy = SheddingPolicy.SHAVE_PEAKS
    hydro_pricing_mode: HydroPricingMode = HydroPricingMode.FAST
    hydro_heuristic_policy: HydroHeuristicPolicy = HydroHeuristicPolicy.ACCOMMODATE_RULES_CURVES
    unit_commitment_mode: UnitCommitmentMode = UnitCommitmentMode.FAST
    number_of_cores_mode: SimulationCore = SimulationCore.MEDIUM
    day_ahead_reserve_management: ReserveManagement = ReserveManagement.GLOBAL
    renewable_generation_modelling: RenewableGenerationModeling = RenewableGenerationModeling.CLUSTERS
    seed_tsgen_wind: int = 5489
    seed_tsgen_load: int = 1005489
    seed_tsgen_hydro: int = 2005489
    seed_tsgen_thermal: int = 3005489
    seed_tsgen_solar: int = 4005489
    seed_tsnumbers: int = 5005489
    seed_unsupplied_energy_costs: int = 6005489
    seed_spilled_energy_costs: int = 7005489
    seed_thermal_costs: int = 8005489
    seed_hydro_costs: int = 9005489
    seed_initial_reservoir_levels: int = 10005489
    # Field removed in v9.2
    initial_reservoir_levels: Optional[InitialReservoirLevel] = None
    # Field introduced in v9.3
    accurate_shave_peaks_include_short_term_storage: Optional[bool] = None


class AdvancedParametersUpdate(AntaresBaseModel):
    model_config = ConfigDict(alias_generator=to_camel, extra="forbid", populate_by_name=True)

    accuracy_on_correlation: Optional[AccuracyOnCorrelation] = None
    power_fluctuations: Optional[PowerFluctuation] = None
    shedding_policy: Optional[SheddingPolicy] = None
    hydro_pricing_mode: Optional[HydroPricingMode] = None
    hydro_heuristic_policy: Optional[HydroHeuristicPolicy] = None
    unit_commitment_mode: Optional[UnitCommitmentMode] = None
    number_of_cores_mode: Optional[SimulationCore] = None
    day_ahead_reserve_management: Optional[ReserveManagement] = None
    renewable_generation_modelling: Optional[RenewableGenerationModeling] = None
    seed_tsgen_wind: Optional[int] = None
    seed_tsgen_load: Optional[int] = None
    seed_tsgen_hydro: Optional[int] = None
    seed_tsgen_thermal: Optional[int] = None
    seed_tsgen_solar: Optional[int] = None
    seed_tsnumbers: Optional[int] = None
    seed_unsupplied_energy_costs: Optional[int] = None
    seed_spilled_energy_costs: Optional[int] = None
    seed_thermal_costs: Optional[int] = None
    seed_hydro_costs: Optional[int] = None
    seed_initial_reservoir_levels: Optional[int] = None
    initial_reservoir_levels: Optional[InitialReservoirLevel] = None
    accurate_shave_peaks_include_short_term_storage: Optional[bool] = None


def update_advanced_parameters(
    parameters: AdvancedParameters, new_parameters: AdvancedParametersUpdate
) -> AdvancedParameters:
    """
    Updates the advanced parameters according to the provided update data.
    """
    current_properties = parameters.model_dump(mode="json")
    new_properties = new_parameters.model_dump(mode="json", exclude_none=True)
    current_properties.update(new_properties)
    return AdvancedParameters.model_validate(current_properties)


def _check_min_version(data: Any, field: str, version: StudyVersion) -> None:
    if getattr(data, field) is not None:
        raise InvalidFieldForVersionError(f"Field {field} is not a valid field for study version {version}")


def validate_advanced_parameters_against_version(
    version: StudyVersion,
    parameters_data: AdvancedParameters | AdvancedParametersUpdate,
) -> None:
    """
    Validates input advanced parameters data against the provided study versions

    Will raise an InvalidFieldForVersionError if a field is not valid for the given study version.
    """
    if version < STUDY_VERSION_8_8 and parameters_data.unit_commitment_mode == UnitCommitmentMode.MILP:
        raise InvalidFieldForVersionError("Unit commitment mode `MILP` only exists in v8.8+ studies")

    if version < STUDY_VERSION_9_3:
        _check_min_version(parameters_data, "accurate_shave_peaks_include_short_term_storage", version)
        if parameters_data.shedding_policy == SheddingPolicy.ACCURATE_SHAVE_PEAKS:
            raise InvalidFieldForVersionError("Shedding policy `accurate shave peaks` only exists in v9.2+ studies")

    if version >= STUDY_VERSION_9_2:
        _check_min_version(parameters_data, "initial_reservoir_levels", version)


def _initialize_field_default(parameters: AdvancedParameters, field: str, default_value: Any) -> None:
    if getattr(parameters, field) is None:
        setattr(parameters, field, default_value)


def initialize_advanced_parameters(parameters: AdvancedParameters, version: StudyVersion) -> None:
    """
    Set undefined version-specific fields to default values.
    """
    if version < STUDY_VERSION_9_2:
        _initialize_field_default(parameters, "initial_reservoir_levels", InitialReservoirLevel.COLD_START)

    if version >= STUDY_VERSION_9_3:
        _initialize_field_default(parameters, "accurate_shave_peaks_include_short_term_storage", False)
