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
from typing import Any

from antares.study.version import StudyVersion
from pydantic import ConfigDict, Field

from antarest.core.serde import AntaresBaseModel
from antarest.core.utils.string import to_kebab_case
from antarest.study.business.model.config.advanced_parameters_model import (
    AdvancedParameters,
    HydroHeuristicPolicy,
    HydroPricingMode,
    InitialReservoirLevel,
    PowerFluctuation,
    RenewableGenerationModeling,
    ReserveManagement,
    SheddingPolicy,
    SimulationCore,
    UnitCommitmentMode,
    validate_advanced_parameters_against_version,
)


class AdvancedParametersSection(AntaresBaseModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True, alias_generator=to_kebab_case)

    accuracy_on_correlation: bool | None = None
    adequacy_block_size: int | None = None


class SeedParametersSection(AntaresBaseModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True, alias_generator=to_kebab_case)

    seed_tsgen_wind: int | None = None
    seed_tsgen_load: int | None = None
    seed_tsgen_hydro: int | None = None
    seed_tsgen_thermal: int | None = None
    seed_tsgen_solar: int | None = None
    seed_tsnumbers: int | None = None
    seed_unsupplied_energy_costs: int | None = None
    seed_spilled_energy_costs: int | None = None
    seed_thermal_costs: int | None = None
    seed_hydro_costs: int | None = None
    seed_initial_reservoir_levels: int | None = None


class OtherPreferencesSection(AntaresBaseModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True, alias_generator=to_kebab_case)

    initial_reservoir_levels: InitialReservoirLevel | None = None
    power_fluctuations: PowerFluctuation | None = None
    shedding_policy: SheddingPolicy | None = None
    hydro_pricing_mode: HydroPricingMode | None = None
    hydro_heuristic_policy: HydroHeuristicPolicy | None = None
    unit_commitment_mode: UnitCommitmentMode | None = None
    number_of_cores_mode: SimulationCore | None = None
    day_ahead_reserve_management: ReserveManagement | None = None
    renewable_generation_modelling: RenewableGenerationModeling | None = None


class AdvancedParametersFileData(AntaresBaseModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    other_preferences: OtherPreferencesSection | None = Field(default=None, alias="other preferences")
    seed_parameters: SeedParametersSection | None = Field(default=None, alias="seeds - Mersenne Twister")
    advanced_parameters: AdvancedParametersSection | None = Field(default=None, alias="advanced parameters")

    def to_model(self) -> AdvancedParameters:
        raise NotImplementedError

    @classmethod
    def from_model(cls, parameters: AdvancedParameters) -> "AdvancedParametersFileData":
        raise NotImplementedError


def parse_advanced_parameters(version: StudyVersion, data: dict[str, Any]) -> AdvancedParameters:
    parameters = AdvancedParametersFileData.model_validate(data).to_model()
    validate_advanced_parameters_against_version(version, parameters)
    return parameters


def serialize_optimization_preferences(version: StudyVersion, parameters: AdvancedParameters) -> dict[str, Any]:
    validate_advanced_parameters_against_version(version, parameters)
    return AdvancedParametersFileData.from_model(parameters).model_dump(mode="json", by_alias=True, exclude_none=True)
