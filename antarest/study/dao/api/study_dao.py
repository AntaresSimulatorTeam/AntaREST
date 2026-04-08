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
from abc import abstractmethod
from collections.abc import Iterator, Sequence

import polars as pl
from antares.study.version import StudyVersion
from typing_extensions import override

from antarest.study.business.model.area_model import AreaInfo, AreaUI, AreaUIData
from antarest.study.business.model.area_properties_model import AreaProperties
from antarest.study.business.model.binding_constraint_model import BindingConstraint
from antarest.study.business.model.config.adequacy_patch_model import AdequacyPatchParameters
from antarest.study.business.model.config.advanced_parameters_model import AdvancedParameters
from antarest.study.business.model.config.compatibility_parameters_model import CompatibilityParameters
from antarest.study.business.model.config.general_model import GeneralConfig
from antarest.study.business.model.config.optimization_config_model import OptimizationPreferences
from antarest.study.business.model.config.playlist_model import Playlist
from antarest.study.business.model.config.timeseries_config_model import TimeSeriesConfiguration
from antarest.study.business.model.district_model import District
from antarest.study.business.model.hydro_allocation_model import HydroAllocation
from antarest.study.business.model.hydro_correlation_model import HydroCorrelation, HydroCorrelationMatrix
from antarest.study.business.model.hydro_model import HydroManagement, HydroProperties, InflowStructure
from antarest.study.business.model.layer_model import Layer
from antarest.study.business.model.link_model import Link
from antarest.study.business.model.renewable_cluster_model import RenewableCluster
from antarest.study.business.model.scenario_builder_model import AnyScenarios, Ruleset, ScenarioType
from antarest.study.business.model.sts_model import (
    STStorage,
    STStorageAdditionalConstraint,
    STStorageAdditionalConstraintsMap,
)
from antarest.study.business.model.thematic_trimming_model import ThematicTrimming
from antarest.study.business.model.thermal_cluster_model import ThermalCluster
from antarest.study.business.model.user_model import UserResourceDataCreation
from antarest.study.business.model.xpansion_model import (
    XpansionAdequacyCriterion,
    XpansionCandidate,
    XpansionResourceFileType,
    XpansionSettings,
    XpansionSettingsUpdate,
)
from antarest.study.dao.api.adequacy_patch_parameters_dao import (
    AdequacyPatchParametersDao,
    ReadOnlyAdequacyPatchParametersDao,
)
from antarest.study.dao.api.advanced_parameters_dao import AdvancedParametersDao, ReadOnlyAdvancedParametersDao
from antarest.study.dao.api.area_dao import AreaDao, ReadOnlyAreaDao
from antarest.study.dao.api.area_properties_dao import AreaPropertiesDao, ReadOnlyAreaPropertiesDao
from antarest.study.dao.api.binding_constraint_dao import ConstraintDao, ReadOnlyConstraintDao
from antarest.study.dao.api.compatibility_parameters_dao import (
    CompatibilityParametersDao,
    ReadOnlyCompatibilityParametersDao,
)
from antarest.study.dao.api.district_dao import DistrictDao, ReadOnlyDistrictDao
from antarest.study.dao.api.general_config_dao import GeneralConfigDao, ReadOnlyGeneralConfigDao
from antarest.study.dao.api.hydro_dao import HydroDao, ReadOnlyHydroDao
from antarest.study.dao.api.layer_dao import LayerDao, ReadOnlyLayerDao
from antarest.study.dao.api.link_dao import LinkDao, ReadOnlyLinkDao
from antarest.study.dao.api.optimization_preferences_dao import (
    OptimizationPreferencesDao,
    ReadOnlyOptimizationPreferencesDao,
)
from antarest.study.dao.api.playlist_config_dao import PlaylistConfigDao, ReadOnlyPlaylistConfigDao
from antarest.study.dao.api.renewable_dao import ReadOnlyRenewableDao, RenewableDao
from antarest.study.dao.api.scenario_builder_dao import ReadOnlyScenarioBuilderDao, ScenarioBuilderDao
from antarest.study.dao.api.st_storage_dao import ReadOnlySTStorageDao, STStorageDao
from antarest.study.dao.api.thematic_trimming_dao import ReadOnlyThematicTrimmingDao, ThematicTrimmingDao
from antarest.study.dao.api.thermal_dao import ReadOnlyThermalDao, ThermalDao
from antarest.study.dao.api.timeseries_config_dao import ReadOnlyTimeSeriesConfigDao, TimeSeriesConfigDao
from antarest.study.dao.api.user_resources_dao import ReadOnlyUserResourcesDao, UserResourcesDao
from antarest.study.dao.api.xpansion_dao import ReadOnlyXpansionDao, XpansionDao
from antarest.study.dao.common import ThermalSeriesMapping
from antarest.study.model import StudyMetadataUpdate
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy


class ReadOnlyStudyDao(
    ReadOnlyLinkDao,
    ReadOnlyThermalDao,
    ReadOnlyRenewableDao,
    ReadOnlyConstraintDao,
    ReadOnlySTStorageDao,
    ReadOnlyHydroDao,
    ReadOnlyGeneralConfigDao,
    ReadOnlyOptimizationPreferencesDao,
    ReadOnlyAdvancedParametersDao,
    ReadOnlyCompatibilityParametersDao,
    ReadOnlyXpansionDao,
    ReadOnlyThematicTrimmingDao,
    ReadOnlyAdequacyPatchParametersDao,
    ReadOnlyTimeSeriesConfigDao,
    ReadOnlyDistrictDao,
    ReadOnlyLayerDao,
    ReadOnlyPlaylistConfigDao,
    ReadOnlyUserResourcesDao,
    ReadOnlyAreaPropertiesDao,
    ReadOnlyScenarioBuilderDao,
    ReadOnlyAreaDao,
):
    @abstractmethod
    def get_version(self) -> StudyVersion:
        raise NotImplementedError()

    @abstractmethod
    def get_comments(self) -> str:
        raise NotImplementedError()


class StudyDao(
    ReadOnlyStudyDao,
    LinkDao,
    ThermalDao,
    RenewableDao,
    ConstraintDao,
    STStorageDao,
    HydroDao,
    GeneralConfigDao,
    OptimizationPreferencesDao,
    AdvancedParametersDao,
    CompatibilityParametersDao,
    XpansionDao,
    ThematicTrimmingDao,
    AdequacyPatchParametersDao,
    TimeSeriesConfigDao,
    DistrictDao,
    LayerDao,
    PlaylistConfigDao,
    UserResourcesDao,
    ScenarioBuilderDao,
    AreaPropertiesDao,
    AreaDao,
):
    """
    Abstraction for access to study data. Handles all reading
    and writing from underlying storage format.
    """

    def read_only(self) -> ReadOnlyStudyDao:
        """
        Returns a read only version of this DAO,
        to ensure it's not used for writing.
        """
        return ReadOnlyAdapter(self)

    @abstractmethod
    def get_file_study(self) -> FileStudy:
        """
        To ease transition, to be removed when all goes through other methods
        """
        raise NotImplementedError()

    @abstractmethod
    def save_comments(self, comments: str) -> None:
        raise NotImplementedError()

    @abstractmethod
    def update_antares_file(self, metadata: StudyMetadataUpdate) -> None:
        """
        Update the study.antares file

        For file-based storage, this updates the actual file.
        For database storage, this is a no-op (metadata is stored in DB).

        Args:
            metadata: The StudyMetadata object to use
        """
        raise NotImplementedError()


class ReadOnlyAdapter(ReadOnlyStudyDao):
    """
    Adapts a full DAO as a read only DAO without modification methods.
    """

    def __init__(self, adaptee: StudyDao):
        self._adaptee = adaptee

    @override
    def get_version(self) -> StudyVersion:
        return self._adaptee.get_version()

    @override
    def get_comments(self) -> str:
        return self._adaptee.get_comments()

    @override
    def get_links(self) -> Sequence[Link]:
        return self._adaptee.get_links()

    @override
    def get_link(self, area1_id: str, area2_id: str) -> Link:
        return self._adaptee.get_link(area1_id, area2_id)

    @override
    def link_exists(self, area1_id: str, area2_id: str) -> bool:
        return self._adaptee.link_exists(area1_id, area2_id)

    @override
    def get_link_indirect_capacities(self, area_from: str, area_to: str) -> pl.DataFrame:
        return self._adaptee.get_link_indirect_capacities(area_from, area_to)

    @override
    def get_link_direct_capacities(self, area_from: str, area_to: str) -> pl.DataFrame:
        return self._adaptee.get_link_direct_capacities(area_from, area_to)

    @override
    def get_link_series(self, area_from: str, area_to: str) -> pl.DataFrame:
        return self._adaptee.get_link_series(area_from, area_to)

    @override
    def get_all_thermals(self) -> dict[str, dict[str, ThermalCluster]]:
        return self._adaptee.get_all_thermals()

    @override
    def get_all_thermals_for_area(self, area_id: str) -> Sequence[ThermalCluster]:
        return self._adaptee.get_all_thermals_for_area(area_id)

    @override
    def get_thermal(self, area_id: str, thermal_id: str) -> ThermalCluster:
        return self._adaptee.get_thermal(area_id, thermal_id)

    @override
    def thermal_exists(self, area_id: str, thermal_id: str) -> bool:
        return self._adaptee.thermal_exists(area_id, thermal_id)

    @override
    def get_thermal_prepro(self, area_id: str, thermal_id: str) -> pl.DataFrame:
        return self._adaptee.get_thermal_prepro(area_id, thermal_id)

    @override
    def get_thermal_modulation(self, area_id: str, thermal_id: str) -> pl.DataFrame:
        return self._adaptee.get_thermal_modulation(area_id, thermal_id)

    @override
    def get_thermal_series(self, area_id: str, thermal_id: str) -> pl.DataFrame:
        return self._adaptee.get_thermal_series(area_id, thermal_id)

    @override
    def get_thermal_fuel_cost(self, area_id: str, thermal_id: str) -> pl.DataFrame:
        return self._adaptee.get_thermal_fuel_cost(area_id, thermal_id)

    @override
    def get_thermal_co2_cost(self, area_id: str, thermal_id: str) -> pl.DataFrame:
        return self._adaptee.get_thermal_co2_cost(area_id, thermal_id)

    @override
    def get_all_thermals_co2_cost(self) -> ThermalSeriesMapping:
        return self._adaptee.get_all_thermals_co2_cost()

    @override
    def get_all_thermals_fuel_cost(self) -> ThermalSeriesMapping:
        return self._adaptee.get_all_thermals_fuel_cost()

    @override
    def get_all_thermals_series(self) -> ThermalSeriesMapping:
        return self._adaptee.get_all_thermals_series()

    @override
    def get_all_thermals_modulation(self) -> ThermalSeriesMapping:
        return self._adaptee.get_all_thermals_modulation()

    @override
    def get_all_thermals_prepro(self) -> ThermalSeriesMapping:
        return self._adaptee.get_all_thermals_prepro()

    @override
    def get_all_renewables(self) -> dict[str, dict[str, RenewableCluster]]:
        return self._adaptee.get_all_renewables()

    @override
    def get_all_renewables_for_area(self, area_id: str) -> Sequence[RenewableCluster]:
        return self._adaptee.get_all_renewables_for_area(area_id)

    @override
    def get_renewable(self, area_id: str, renewable_id: str) -> RenewableCluster:
        return self._adaptee.get_renewable(area_id, renewable_id)

    @override
    def renewable_exists(self, area_id: str, renewable_id: str) -> bool:
        return self._adaptee.renewable_exists(area_id, renewable_id)

    @override
    def get_renewable_series(self, area_id: str, renewable_id: str) -> pl.DataFrame:
        return self._adaptee.get_renewable_series(area_id, renewable_id)

    @override
    def get_all_constraints(self) -> dict[str, BindingConstraint]:
        return self._adaptee.get_all_constraints()

    @override
    def get_constraint(self, constraint_id: str) -> BindingConstraint:
        return self._adaptee.get_constraint(constraint_id)

    @override
    def get_constraint_values_matrix(self, constraint_id: str) -> pl.DataFrame:
        return self._adaptee.get_constraint_values_matrix(constraint_id)

    @override
    def get_constraint_less_term_matrix(self, constraint_id: str) -> pl.DataFrame:
        return self._adaptee.get_constraint_less_term_matrix(constraint_id)

    @override
    def get_constraint_greater_term_matrix(self, constraint_id: str) -> pl.DataFrame:
        return self._adaptee.get_constraint_greater_term_matrix(constraint_id)

    @override
    def get_constraint_equal_term_matrix(self, constraint_id: str) -> pl.DataFrame:
        return self._adaptee.get_constraint_equal_term_matrix(constraint_id)

    @override
    def get_all_st_storages(self) -> dict[str, dict[str, STStorage]]:
        return self._adaptee.get_all_st_storages()

    @override
    def get_all_st_storages_for_area(self, area_id: str) -> Sequence[STStorage]:
        return self._adaptee.get_all_st_storages_for_area(area_id)

    @override
    def get_st_storage(self, area_id: str, storage_id: str) -> STStorage:
        return self._adaptee.get_st_storage(area_id, storage_id)

    @override
    def st_storage_exists(self, area_id: str, storage_id: str) -> bool:
        return self._adaptee.st_storage_exists(area_id, storage_id)

    @override
    def get_st_storage_pmax_injection(self, area_id: str, storage_id: str) -> pl.DataFrame:
        return self._adaptee.get_st_storage_pmax_injection(area_id, storage_id)

    @override
    def get_st_storage_pmax_withdrawal(self, area_id: str, storage_id: str) -> pl.DataFrame:
        return self._adaptee.get_st_storage_pmax_withdrawal(area_id, storage_id)

    @override
    def get_st_storage_lower_rule_curve(self, area_id: str, storage_id: str) -> pl.DataFrame:
        return self._adaptee.get_st_storage_lower_rule_curve(area_id, storage_id)

    @override
    def get_st_storage_upper_rule_curve(self, area_id: str, storage_id: str) -> pl.DataFrame:
        return self._adaptee.get_st_storage_upper_rule_curve(area_id, storage_id)

    @override
    def get_st_storage_inflows(self, area_id: str, storage_id: str) -> pl.DataFrame:
        return self._adaptee.get_st_storage_inflows(area_id, storage_id)

    @override
    def get_st_storage_cost_injection(self, area_id: str, storage_id: str) -> pl.DataFrame:
        return self._adaptee.get_st_storage_cost_injection(area_id, storage_id)

    @override
    def get_st_storage_cost_withdrawal(self, area_id: str, storage_id: str) -> pl.DataFrame:
        return self._adaptee.get_st_storage_cost_withdrawal(area_id, storage_id)

    @override
    def get_st_storage_cost_level(self, area_id: str, storage_id: str) -> pl.DataFrame:
        return self._adaptee.get_st_storage_cost_level(area_id, storage_id)

    @override
    def get_st_storage_cost_variation_injection(self, area_id: str, storage_id: str) -> pl.DataFrame:
        return self._adaptee.get_st_storage_cost_variation_injection(area_id, storage_id)

    @override
    def get_st_storage_cost_variation_withdrawal(self, area_id: str, storage_id: str) -> pl.DataFrame:
        return self._adaptee.get_st_storage_cost_variation_withdrawal(area_id, storage_id)

    @override
    def get_st_storage_additional_constraint_matrix(
        self, area_id: str, storage_id: str, constraint_id: str
    ) -> pl.DataFrame:
        return self._adaptee.get_st_storage_additional_constraint_matrix(area_id, storage_id, constraint_id)

    @override
    def get_all_hydro_properties(self) -> dict[str, HydroProperties]:
        return self._adaptee.get_all_hydro_properties()

    @override
    def get_hydro_management(self, area_id: str) -> HydroManagement:
        return self._adaptee.get_hydro_management(area_id)

    @override
    def get_inflow_structure(self, area_id: str) -> InflowStructure:
        return self._adaptee.get_inflow_structure(area_id)

    @override
    def get_hydro_allocation(self, area_id: str) -> HydroAllocation:
        return self._adaptee.get_hydro_allocation(area_id)

    @override
    def get_hydro_allocation_matrix(self) -> dict[str, HydroAllocation]:
        return self._adaptee.get_hydro_allocation_matrix()

    @override
    def get_hydro_correlation(self, area_id: str) -> HydroCorrelation:
        return self._adaptee.get_hydro_correlation(area_id)

    @override
    def get_hydro_correlation_matrix(self) -> HydroCorrelationMatrix:
        return self._adaptee.get_hydro_correlation_matrix()

    @override
    def get_hydro_maxpower(self, area_id: str) -> pl.DataFrame:
        return self._adaptee.get_hydro_maxpower(area_id)

    @override
    def get_hydro_reservoir(self, area_id: str) -> pl.DataFrame:
        return self._adaptee.get_hydro_reservoir(area_id)

    @override
    def get_hydro_energy(self, area_id: str) -> pl.DataFrame:
        return self._adaptee.get_hydro_energy(area_id)

    @override
    def get_hydro_run_of_river(self, area_id: str) -> pl.DataFrame:
        return self._adaptee.get_hydro_run_of_river(area_id)

    @override
    def get_hydro_modulation(self, area_id: str) -> pl.DataFrame:
        return self._adaptee.get_hydro_modulation(area_id)

    @override
    def get_hydro_credit_modulations(self, area_id: str) -> pl.DataFrame:
        return self._adaptee.get_hydro_credit_modulations(area_id)

    @override
    def get_hydro_inflow_pattern(self, area_id: str) -> pl.DataFrame:
        return self._adaptee.get_hydro_inflow_pattern(area_id)

    @override
    def get_hydro_water_values(self, area_id: str) -> pl.DataFrame:
        return self._adaptee.get_hydro_water_values(area_id)

    @override
    def get_hydro_mingen(self, area_id: str) -> pl.DataFrame:
        return self._adaptee.get_hydro_mingen(area_id)

    @override
    def get_general_config(self) -> GeneralConfig:
        return self._adaptee.get_general_config()

    @override
    def get_optimization_preferences(self) -> OptimizationPreferences:
        return self._adaptee.get_optimization_preferences()

    @override
    def get_advanced_parameters(self) -> AdvancedParameters:
        return self._adaptee.get_advanced_parameters()

    @override
    def get_compatibility_parameters(self) -> CompatibilityParameters:
        return self._adaptee.get_compatibility_parameters()

    @override
    def get_all_st_storage_additional_constraints(self) -> STStorageAdditionalConstraintsMap:
        return self._adaptee.get_all_st_storage_additional_constraints()

    @override
    def get_st_storage_additional_constraints(
        self, area_id: str, storage_id: str
    ) -> list[STStorageAdditionalConstraint]:
        return self._adaptee.get_st_storage_additional_constraints(area_id, storage_id)

    @override
    def get_all_xpansion_candidates(self) -> list[XpansionCandidate]:
        return self._adaptee.get_all_xpansion_candidates()

    @override
    def get_xpansion_candidate(self, candidate_id: str) -> XpansionCandidate:
        return self._adaptee.get_xpansion_candidate(candidate_id)

    @override
    def checks_xpansion_candidate_coherence(self, candidate: XpansionCandidate) -> None:
        return self._adaptee.checks_xpansion_candidate_coherence(candidate)

    @override
    def checks_xpansion_candidate_can_be_deleted(self, candidate_name: str) -> None:
        return self._adaptee.checks_xpansion_candidate_can_be_deleted(candidate_name)

    @override
    def get_xpansion_settings(self) -> XpansionSettings:
        return self._adaptee.get_xpansion_settings()

    @override
    def checks_xpansion_settings_are_correct(self, settings: XpansionSettingsUpdate) -> None:
        return self._adaptee.checks_xpansion_settings_are_correct(settings)

    @override
    def get_xpansion_resource(self, resource_type: XpansionResourceFileType, filename: str) -> bytes | pl.DataFrame:
        return self._adaptee.get_xpansion_resource(resource_type, filename)

    @override
    def get_xpansion_resources(self, resource_type: XpansionResourceFileType) -> list[str]:
        return self._adaptee.get_xpansion_resources(resource_type)

    @override
    def checks_xpansion_resource_can_be_deleted(self, resource_type: XpansionResourceFileType, filename: str) -> None:
        return self._adaptee.checks_xpansion_resource_can_be_deleted(resource_type, filename)

    @override
    def get_xpansion_adequacy_criterion(self) -> XpansionAdequacyCriterion:
        return self._adaptee.get_xpansion_adequacy_criterion()

    @override
    def get_thematic_trimming(self) -> ThematicTrimming:
        return self._adaptee.get_thematic_trimming()

    @override
    def get_adequacy_patch_parameters(self) -> AdequacyPatchParameters:
        return self._adaptee.get_adequacy_patch_parameters()

    @override
    def get_timeseries_config(self) -> TimeSeriesConfiguration:
        return self._adaptee.get_timeseries_config()

    @override
    def get_district(self, district_id: str) -> District:
        return self._adaptee.get_district(district_id)

    @override
    def get_districts(self) -> Sequence[District]:
        return self._adaptee.get_districts()

    @override
    def district_exists(self, district_id: str) -> bool:
        return self._adaptee.district_exists(district_id)

    @override
    def get_all_area_ids(self) -> list[str]:
        return self._adaptee.get_all_area_ids()

    @override
    def get_invalid_area_ids(self, areas: list[str]) -> list[str]:
        return self._adaptee.get_invalid_area_ids(areas)

    @override
    def get_layers(self) -> Sequence[Layer]:
        return self._adaptee.get_layers()

    @override
    def layer_exists(self, layer_id: str) -> bool:
        return self._adaptee.layer_exists(layer_id)

    @override
    def get_playlist_config(self) -> Playlist:
        return self._adaptee.get_playlist_config()

    @override
    def get_area_properties(self, area_id: str) -> AreaProperties:
        return self._adaptee.get_area_properties(area_id)

    @override
    def get_all_area_properties(self) -> dict[str, AreaProperties]:
        return self._adaptee.get_all_area_properties()

    @override
    def get_ruleset(self) -> Ruleset:
        return self._adaptee.get_ruleset()

    @override
    def get_scenario_by_type(self, scenario_type: ScenarioType) -> AnyScenarios:
        return self._adaptee.get_scenario_by_type(scenario_type)

    @override
    def get_all_areas_info(self) -> list[AreaInfo]:
        return self._adaptee.get_all_areas_info()

    @override
    def get_all_areas_ui_info(self) -> dict[str, AreaUIData]:
        return self._adaptee.get_all_areas_ui_info()

    @override
    def get_area_ui(self, area_id: str, layer: str = "0") -> AreaUI:
        return self._adaptee.get_area_ui(area_id, layer)

    @override
    def get_all_user_resources(self) -> Iterator[UserResourceDataCreation]:
        return self._adaptee.get_all_user_resources()

    @override
    def get_load(self, area_id: str) -> pl.DataFrame:
        return self._adaptee.get_load(area_id)

    @override
    def get_misc_gen(self, area_id: str) -> pl.DataFrame:
        return self._adaptee.get_misc_gen(area_id)

    @override
    def get_reserves(self, area_id: str) -> pl.DataFrame:
        return self._adaptee.get_reserves(area_id)

    @override
    def get_solar(self, area_id: str) -> pl.DataFrame:
        return self._adaptee.get_solar(area_id)

    @override
    def get_wind(self, area_id: str) -> pl.DataFrame:
        return self._adaptee.get_wind(area_id)

    @override
    def get_hydro_max_hourly_gen_power(self, area_id: str) -> pl.DataFrame:
        return self._adaptee.get_hydro_max_hourly_gen_power(area_id)

    @override
    def get_hydro_max_hourly_pump_power(self, area_id: str) -> pl.DataFrame:
        return self._adaptee.get_hydro_max_hourly_pump_power(area_id)

    @override
    def get_hydro_max_daily_gen_energy(self, area_id: str) -> pl.DataFrame:
        return self._adaptee.get_hydro_max_daily_gen_energy(area_id)

    @override
    def get_hydro_max_daily_pump_energy(self, area_id: str) -> pl.DataFrame:
        return self._adaptee.get_hydro_max_daily_pump_energy(area_id)
