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
from dataclasses import dataclass, field
from enum import Enum
from typing import Generic, TypeVar

T = TypeVar("T")


@dataclass(frozen=True)
class CommandOutput(Generic[T]):
    status: bool
    message: str
    # Result of the command to be used by the managers to return the application result.
    result: T | None = None
    # If the command cannot guarantee the study config is still valid after it was applied, this should be set to True.
    should_invalidate_cache: bool = False


def command_failed(message: str) -> CommandOutput[T]:
    return CommandOutput(False, message)


def command_succeeded(message: str, result: T | None, should_invalidate_cache: bool = False) -> CommandOutput[T]:
    return CommandOutput(True, message, result, should_invalidate_cache)


class FilteringOptions:
    FILTER_SYNTHESIS: str = "hourly, daily, weekly, monthly, annual"
    FILTER_YEAR_BY_YEAR: str = "hourly, daily, weekly, monthly, annual"


class CommandName(Enum):
    CREATE_AREA = "create_area"
    UPDATE_AREAS_PROPERTIES = "update_areas_properties"
    UPDATE_AREA_UI = "update_area_ui"
    REMOVE_AREA = "remove_area"
    CREATE_LAYER = "create_layer"
    REMOVE_LAYER = "remove_layer"
    UPDATE_LAYER = "update_layer"
    REPLACE_LAYER_AREAS = "replace_layer_areas"
    CREATE_DISTRICT = "create_district"
    REMOVE_DISTRICT = "remove_district"
    CREATE_LINK = "create_link"
    UPDATE_LINK = "update_link"
    REMOVE_LINK = "remove_link"
    CREATE_BINDING_CONSTRAINT = "create_binding_constraint"
    UPDATE_BINDING_CONSTRAINT = "update_binding_constraint"
    REMOVE_BINDING_CONSTRAINT = "remove_binding_constraint"
    UPDATE_BINDING_CONSTRAINTS = "update_binding_constraints"
    REMOVE_MULTIPLE_BINDING_CONSTRAINTS = "remove_multiple_binding_constraints"
    CREATE_THERMAL_CLUSTER = "create_cluster"
    REMOVE_THERMAL_CLUSTER = "remove_cluster"
    UPDATE_THERMAL_CLUSTERS = "update_thermal_clusters"
    CREATE_RENEWABLES_CLUSTER = "create_renewables_cluster"
    REMOVE_RENEWABLES_CLUSTER = "remove_renewables_cluster"
    UPDATE_RENEWABLES_CLUSTERS = "update_renewables_clusters"
    CREATE_ST_STORAGE = "create_st_storage"
    CREATE_ST_STORAGE_ADDITIONAL_CONSTRAINTS = "create_st_storage_additional_constraints"
    REMOVE_ST_STORAGE = "remove_st_storage"
    REMOVE_MULTIPLE_ST_STORAGE_ADDITIONAL_CONSTRAINTS = "remove_st_storage_additional_constraints"
    UPDATE_ST_STORAGES = "update_st_storages"
    UPDATE_ST_STORAGE_ADDITIONAL_CONSTRAINTS = "update_st_storage_additional_constraints"
    UPDATE_HYDRO_PROPERTIES = "update_hydro_properties"
    UPDATE_INFLOW_STRUCTURE = "update_inflow_structure"
    REPLACE_MATRIX = "replace_matrix"
    UPDATE_CONFIG = "update_config"
    UPDATE_COMMENTS = "update_comments"
    REPLACE_COMMENTS = "replace_comments"
    UPDATE_FILE = "update_file"
    UPDATE_DISTRICT = "update_district"
    UPDATE_PLAYLIST = "update_playlist"
    UPDATE_SCENARIO_BUILDER = "update_scenario_builder"
    GENERATE_THERMAL_CLUSTER_TIMESERIES = "generate_thermal_cluster_timeseries"
    CREATE_USER_RESOURCE = "create_user_resource"
    REPLACE_USER_RESOURCE = "replace_user_resource"
    REMOVE_USER_RESOURCE = "remove_user_resource"
    REMOVE_XPANSION_CONFIGURATION = "remove_xpansion_configuration"
    REMOVE_XPANSION_RESOURCE = "remove_xpansion_resource"
    CREATE_XPANSION_CONFIGURATION = "create_xpansion_configuration"
    CREATE_XPANSION_CAPACITY = "create_xpansion_capacity"
    CREATE_XPANSION_WEIGHT = "create_xpansion_weight"
    CREATE_XPANSION_CONSTRAINT = "create_xpansion_constraint"
    CREATE_XPANSION_CANDIDATE = "create_xpansion_candidate"
    REMOVE_XPANSION_CANDIDATE = "remove_xpansion_candidate"
    REPLACE_XPANSION_CANDIDATE = "replace_xpansion_candidate"
    UPDATE_XPANSION_SETTINGS = "update_xpansion_settings"
    REPLACE_XPANSION_ADEQUACY_CRITERION = "replace_xpansion_adequacy_criterion"
    UPDATE_GENERAL_CONFIG = "update_general_config"
    UPDATE_OPTIMIZATION_PREFERENCES = "update_optimization_preferences"
    UPDATE_ADVANCED_PARAMETERS = "update_advanced_parameters"
    UPDATE_THEMATIC_TRIMMING = "update_thematic_trimming"
    UPDATE_ADEQUACY_PATCH_PARAMETERS = "update_adequacy_patch_parameters"
    UPDATE_TIMESERIES_CONFIG = "update_time"
    REPLACE_HYDRO_ALLOCATION = "replace_hydro_allocation"
    REPLACE_HYDRO_CORRELATION = "replace_hydro_correlation"
    CONVERT_HYDRO_PMAX = "convert_hydro_pmax"
    UPDATE_RESERVES_ENABLED = "update_reserves_enabled"
    UPDATE_RESERVES_GLOBAL_PARAMETERS = "update_reserves_global_parameters"
    CREATE_RESERVE_DEFINITION = "create_reserve_definition"
    UPDATE_RESERVE_DEFINITIONS = "update_reserve_definitions"
    REMOVE_RESERVE_DEFINITIONS = "remove_reserve_definitions"
    CREATE_THERMAL_CLUSTER_RESERVE_PARTICIPATION = "create_thermal_cluster_reserve_participation"
    UPDATE_THERMAL_CLUSTER_RESERVE_PARTICIPATIONS = "update_thermal_cluster_reserve_participations"
    REMOVE_THERMAL_CLUSTER_RESERVE_PARTICIPATIONS = "remove_thermal_cluster_reserve_participations"


@dataclass(frozen=True)
class InnerMatrices:
    matrices: list[str] = field(default_factory=list)
    # If the command generates matrices at the runtime, it cannot return them in the `matrices` attribute. If so, we should check the variant snapshot.
    generates_matrices_at_run_time: bool = False
