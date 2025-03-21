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
import math
from typing import Any, Dict, List

from pydantic import field_validator
from pydantic.types import StrictInt, StrictStr

from antarest.core.exceptions import InvalidFieldForVersionError
from antarest.study.business.all_optional_meta import all_optional_model
from antarest.study.business.enum_ignore_case import EnumIgnoreCase
from antarest.study.business.study_interface import StudyInterface
from antarest.study.business.utils import GENERAL_DATA_PATH, FieldInfo, FormFieldsBaseModel
from antarest.study.model import STUDY_VERSION_8_8, STUDY_VERSION_9_2
from antarest.study.storage.variantstudy.model.command.update_config import UpdateConfig
from antarest.study.storage.variantstudy.model.command_context import CommandContext


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


@all_optional_model
class AdvancedParamsFormFields(FormFieldsBaseModel):
    # Advanced parameters
    accuracy_on_correlation: StrictStr
    # Other preferences
    initial_reservoir_levels: InitialReservoirLevel
    power_fluctuations: PowerFluctuation
    shedding_policy: SheddingPolicy
    hydro_pricing_mode: HydroPricingMode
    hydro_heuristic_policy: HydroHeuristicPolicy
    unit_commitment_mode: UnitCommitmentMode
    number_of_cores_mode: SimulationCore
    day_ahead_reserve_management: ReserveManagement
    renewable_generation_modelling: RenewableGenerationModeling
    # Seeds
    seed_tsgen_wind: StrictInt
    seed_tsgen_load: StrictInt
    seed_tsgen_hydro: StrictInt
    seed_tsgen_thermal: StrictInt
    seed_tsgen_solar: StrictInt
    seed_tsnumbers: StrictInt
    seed_unsupplied_energy_costs: StrictInt
    seed_spilled_energy_costs: StrictInt
    seed_thermal_costs: StrictInt
    seed_hydro_costs: StrictInt
    seed_initial_reservoir_levels: StrictInt

    @field_validator("accuracy_on_correlation")
    def check_accuracy_on_correlation(cls, v: str) -> str:
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


ADVANCED_PARAMS_PATH = f"{GENERAL_DATA_PATH}/advanced parameters"
OTHER_PREFERENCES_PATH = f"{GENERAL_DATA_PATH}/other preferences"
SEEDS_PATH = f"{GENERAL_DATA_PATH}/seeds - Mersenne Twister"


FIELDS_INFO: Dict[str, FieldInfo] = {
    # Advanced parameters
    "accuracy_on_correlation": {
        "path": f"{ADVANCED_PARAMS_PATH}/accuracy-on-correlation",
        "default_value": "",
    },
    # Other preferences
    "initial_reservoir_levels": {
        "path": f"{OTHER_PREFERENCES_PATH}/initial-reservoir-levels",
        "default_value": InitialReservoirLevel.COLD_START.value,
        "end_version": STUDY_VERSION_9_2,
    },
    "power_fluctuations": {
        "path": f"{OTHER_PREFERENCES_PATH}/power-fluctuations",
        "default_value": PowerFluctuation.FREE_MODULATIONS.value,
    },
    "shedding_policy": {
        "path": f"{OTHER_PREFERENCES_PATH}/shedding-policy",
        "default_value": SheddingPolicy.SHAVE_PEAKS.value,
    },
    "hydro_pricing_mode": {
        "path": f"{OTHER_PREFERENCES_PATH}/hydro-pricing-mode",
        "default_value": HydroPricingMode.FAST.value,
    },
    "hydro_heuristic_policy": {
        "path": f"{OTHER_PREFERENCES_PATH}/hydro-heuristic-policy",
        "default_value": HydroHeuristicPolicy.ACCOMMODATE_RULES_CURVES.value,
    },
    "unit_commitment_mode": {
        "path": f"{OTHER_PREFERENCES_PATH}/unit-commitment-mode",
        "default_value": UnitCommitmentMode.FAST.value,
    },
    "number_of_cores_mode": {
        "path": f"{OTHER_PREFERENCES_PATH}/number-of-cores-mode",
        "default_value": SimulationCore.MEDIUM.value,
    },
    "day_ahead_reserve_management": {
        "path": f"{OTHER_PREFERENCES_PATH}/day-ahead-reserve-management",
        "default_value": ReserveManagement.GLOBAL.value,
    },
    "renewable_generation_modelling": {
        "path": f"{OTHER_PREFERENCES_PATH}/renewable-generation-modelling",
        "default_value": RenewableGenerationModeling.CLUSTERS.value,
    },
    # Seeds
    "seed_tsgen_wind": {
        "path": f"{SEEDS_PATH}/seed-tsgen-wind",
        "default_value": 5489,
    },
    "seed_tsgen_load": {
        "path": f"{SEEDS_PATH}/seed-tsgen-load",
        "default_value": 1005489,
    },
    "seed_tsgen_hydro": {
        "path": f"{SEEDS_PATH}/seed-tsgen-hydro",
        "default_value": 2005489,
    },
    "seed_tsgen_thermal": {
        "path": f"{SEEDS_PATH}/seed-tsgen-thermal",
        "default_value": 3005489,
    },
    "seed_tsgen_solar": {
        "path": f"{SEEDS_PATH}/seed-tsgen-solar",
        "default_value": 4005489,
    },
    "seed_tsnumbers": {
        "path": f"{SEEDS_PATH}/seed-tsnumbers",
        "default_value": 5005489,
    },
    "seed_unsupplied_energy_costs": {
        "path": f"{SEEDS_PATH}/seed-unsupplied-energy-costs",
        "default_value": 6005489,
    },
    "seed_spilled_energy_costs": {
        "path": f"{SEEDS_PATH}/seed-spilled-energy-costs",
        "default_value": 7005489,
    },
    "seed_thermal_costs": {
        "path": f"{SEEDS_PATH}/seed-thermal-costs",
        "default_value": 8005489,
    },
    "seed_hydro_costs": {
        "path": f"{SEEDS_PATH}/seed-hydro-costs",
        "default_value": 9005489,
    },
    "seed_initial_reservoir_levels": {
        "path": f"{SEEDS_PATH}/seed-initial-reservoir-levels",
        "default_value": 10005489,
    },
}


class AdvancedParamsManager:
    def __init__(self, command_context: CommandContext) -> None:
        self._command_context = command_context

    def get_field_values(self, study: StudyInterface) -> AdvancedParamsFormFields:
        """
        Get Advanced parameters values for the webapp form
        """
        file_study = study.get_files()
        general_data = file_study.tree.get(GENERAL_DATA_PATH.split("/"))
        advanced_params = general_data.get("advanced parameters", {})
        other_preferences = general_data.get("other preferences", {})
        seeds = general_data.get("seeds - Mersenne Twister", {})

        def get_value(field_info: FieldInfo) -> Any:
            start_version = field_info.get("start_version", 0)
            end_version = field_info.get("end_version", math.inf)
            is_in_version = study.version >= start_version and file_study.config.version < end_version
            if not is_in_version:
                return None

            path = field_info["path"]
            target_name = path.split("/")[-1]
            if ADVANCED_PARAMS_PATH in path:
                parent = advanced_params
            elif OTHER_PREFERENCES_PATH in path:
                parent = other_preferences
            else:
                parent = seeds
            return parent.get(target_name, field_info["default_value"])

        return AdvancedParamsFormFields.model_construct(**{name: get_value(info) for name, info in FIELDS_INFO.items()})

    def set_field_values(self, study: StudyInterface, field_values: AdvancedParamsFormFields) -> None:
        """
        Set Advanced parameters values from the webapp form
        """
        commands: List[UpdateConfig] = []

        for field_name, value in field_values.__iter__():
            if value is not None:
                info = FIELDS_INFO[field_name]

                # Handle the specific case of `milp` value that appeared in v8.8
                if (
                    field_name == "unit_commitment_mode"
                    and value == UnitCommitmentMode.MILP
                    and study.version < STUDY_VERSION_8_8
                ):
                    raise InvalidFieldForVersionError("Unit commitment mode `MILP` only exists in v8.8+ studies")

                commands.append(
                    UpdateConfig(
                        target=info["path"],
                        data=value,
                        command_context=self._command_context,
                        study_version=study.version,
                    )
                )

        if len(commands) > 0:
            study.add_commands(commands)
