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

"""
Database implementation of StudyDao using SQLAlchemy.

This DAO provides database-backed storage for studies when storage_mode=DATABASE.
Uses multiple inheritance to combine specialized DAOs (like FileStudyTreeDao).
"""

from pathlib import PurePosixPath
from typing import Dict, Iterator, Optional, Self, Sequence

import polars as pl
from antares.study.version import StudyVersion
from sqlalchemy import select
from sqlalchemy.orm import Session
from typing_extensions import override

from antarest.study.business.model.binding_constraint_model import BindingConstraint
from antarest.study.business.model.config.adequacy_patch_model import AdequacyPatchParameters
from antarest.study.business.model.config.advanced_parameters_model import AdvancedParameters
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
from antarest.study.business.model.scenario_builder_model import AnyScenarios, Rulesets, ScenarioType
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
from antarest.study.dao.api.study_dao import StudyDao
from antarest.study.dao.database.database_area_dao import DatabaseAreaDao
from antarest.study.dao.database.database_area_properties_dao import DatabaseAreaPropertiesDao
from antarest.study.model import Study
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy


class DatabaseStudyDao(StudyDao, DatabaseAreaDao, DatabaseAreaPropertiesDao):
    """
    Database implementation of StudyDao.

    Note: Write operations do NOT commit transactions. The caller (service layer)
    is responsible for transaction management (commit/rollback).
    This allows combining multiple DAO operations into a single atomic transaction.
    """

    def __init__(self, study_id: str, db_session: Session) -> None:
        """
        Initialize DatabaseStudyDao.

        Args:
            study_id: The study ID for database queries
            db_session: SQLAlchemy session for database operations
        """
        DatabaseAreaDao.__init__(self, study_id, db_session)
        DatabaseAreaPropertiesDao.__init__(self, study_id, db_session)

    # Implementation of abstract methods required by StudyDao
    @override
    def get_version(self) -> StudyVersion:
        """
        Get the study version from the database.

        Returns:
            The study version.
        """
        stmt = select(Study.version).where(Study.id == self._study_id)
        version_str = self._db_session.execute(stmt).scalar_one()
        return StudyVersion.parse(version_str)

    @override
    def get_impl(self) -> Self:
        return self

    @override
    def get_comments(self) -> str:
        raise NotImplementedError("This method is not yet implemented for database storage mode")

    @override
    def save_comments(self, comments: str) -> None:
        raise NotImplementedError("This method is not yet implemented for database storage mode")

    @override
    def update_antares_file(self, editor: str, last_save: float) -> None:
        pass

    @override
    def get_file_study(self) -> FileStudy:
        """
        Get the FileStudy instance.

        Note: FileStudy is not available in database mode.

        Raises:
            NotImplementedError: Always raised as FileStudy is not supported in database mode.
        """
        raise NotImplementedError(
            "get_file_study() is not supported in database storage mode. Use database-specific methods instead."
        )

    @override
    def save_link(self, link: Link) -> None:
        raise NotImplementedError("This method is not yet implemented for database storage mode")

    @override
    def save_link_indirect_capacities(self, area_from: str, area_to: str, series_id: str) -> None:
        raise NotImplementedError("This method is not yet implemented for database storage mode")

    @override
    def save_link_direct_capacities(self, area_from: str, area_to: str, series_id: str) -> None:
        raise NotImplementedError("This method is not yet implemented for database storage mode")

    @override
    def save_link_series(self, area_from: str, area_to: str, series_id: str) -> None:
        raise NotImplementedError("This method is not yet implemented for database storage mode")

    @override
    def delete_link(self, link: Link) -> None:
        raise NotImplementedError("This method is not yet implemented for database storage mode")

    @override
    def get_links(self) -> Sequence[Link]:
        raise NotImplementedError("This method is not yet implemented for database storage mode")

    @override
    def get_link(self, area1_id: str, area2_id: str) -> Link:
        raise NotImplementedError("This method is not yet implemented for database storage mode")

    @override
    def link_exists(self, area1_id: str, area2_id: str) -> bool:
        raise NotImplementedError("This method is not yet implemented for database storage mode")

    @override
    def save_thermal(self, area_id: str, thermal: ThermalCluster) -> None:
        raise NotImplementedError("This method is not yet implemented for database storage mode")

    @override
    def save_thermals(self, area_id: str, thermals: Sequence[ThermalCluster]) -> None:
        raise NotImplementedError("This method is not yet implemented for database storage mode")

    @override
    def save_thermal_prepro(self, area_id: str, thermal_id: str, series_id: str) -> None:
        raise NotImplementedError("This method is not yet implemented for database storage mode")

    @override
    def save_thermal_modulation(self, area_id: str, thermal_id: str, series_id: str) -> None:
        raise NotImplementedError("This method is not yet implemented for database storage mode")

    @override
    def save_thermal_series(self, area_id: str, thermal_id: str, series_id: str) -> None:
        raise NotImplementedError("This method is not yet implemented for database storage mode")

    @override
    def save_thermal_fuel_cost(self, area_id: str, thermal_id: str, series_id: str) -> None:
        raise NotImplementedError("This method is not yet implemented for database storage mode")

    @override
    def save_thermal_co2_cost(self, area_id: str, thermal_id: str, series_id: str) -> None:
        raise NotImplementedError("This method is not yet implemented for database storage mode")

    @override
    def delete_thermal(self, area_id: str, thermal: ThermalCluster) -> None:
        raise NotImplementedError("This method is not yet implemented for database storage mode")

    @override
    def get_all_thermals(self) -> dict[str, dict[str, ThermalCluster]]:
        raise NotImplementedError("This method is not yet implemented for database storage mode")

    @override
    def get_all_thermals_for_area(self, area_id: str) -> Sequence[ThermalCluster]:
        raise NotImplementedError("This method is not yet implemented for database storage mode")

    @override
    def get_thermal(self, area_id: str, thermal_id: str) -> ThermalCluster:
        raise NotImplementedError("This method is not yet implemented for database storage mode")

    @override
    def thermal_exists(self, area_id: str, thermal_id: str) -> bool:
        raise NotImplementedError("This method is not yet implemented for database storage mode")

    @override
    def get_thermal_prepro(self, area_id: str, thermal_id: str) -> pl.DataFrame:
        raise NotImplementedError("This method is not yet implemented for database storage mode")

    @override
    def get_thermal_modulation(self, area_id: str, thermal_id: str) -> pl.DataFrame:
        raise NotImplementedError("This method is not yet implemented for database storage mode")

    @override
    def get_thermal_series(self, area_id: str, thermal_id: str) -> pl.DataFrame:
        raise NotImplementedError("This method is not yet implemented for database storage mode")

    @override
    def get_thermal_fuel_cost(self, area_id: str, thermal_id: str) -> pl.DataFrame:
        raise NotImplementedError("This method is not yet implemented for database storage mode")

    @override
    def get_thermal_co2_cost(self, area_id: str, thermal_id: str) -> pl.DataFrame:
        raise NotImplementedError("This method is not yet implemented for database storage mode")

    @override
    def save_renewable(self, area_id: str, renewable: RenewableCluster) -> None:
        raise NotImplementedError("This method is not yet implemented for database storage mode")

    @override
    def save_renewables(self, area_id: str, renewables: Sequence[RenewableCluster]) -> None:
        raise NotImplementedError("This method is not yet implemented for database storage mode")

    @override
    def save_renewable_series(self, area_id: str, renewable_id: str, series_id: str) -> None:
        raise NotImplementedError("This method is not yet implemented for database storage mode")

    @override
    def delete_renewable(self, area_id: str, renewable: RenewableCluster) -> None:
        raise NotImplementedError("This method is not yet implemented for database storage mode")

    @override
    def get_all_renewables(self) -> dict[str, dict[str, RenewableCluster]]:
        raise NotImplementedError("This method is not yet implemented for database storage mode")

    @override
    def get_all_renewables_for_area(self, area_id: str) -> Sequence[RenewableCluster]:
        raise NotImplementedError("This method is not yet implemented for database storage mode")

    @override
    def get_renewable(self, area_id: str, renewable_id: str) -> RenewableCluster:
        raise NotImplementedError("This method is not yet implemented for database storage mode")

    @override
    def renewable_exists(self, area_id: str, renewable_id: str) -> bool:
        raise NotImplementedError("This method is not yet implemented for database storage mode")

    @override
    def get_renewable_series(self, area_id: str, renewable_id: str) -> pl.DataFrame:
        raise NotImplementedError("This method is not yet implemented for database storage mode")

    @override
    def save_constraints(self, constraints: Sequence[BindingConstraint]) -> None:
        raise NotImplementedError("This method is not yet implemented for database storage mode")

    @override
    def save_constraint_values_matrix(self, constraint_id: str, series_id: str) -> None:
        raise NotImplementedError("This method is not yet implemented for database storage mode")

    @override
    def save_constraint_less_term_matrix(self, constraint_id: str, series_id: str) -> None:
        raise NotImplementedError("This method is not yet implemented for database storage mode")

    @override
    def save_constraint_greater_term_matrix(self, constraint_id: str, series_id: str) -> None:
        raise NotImplementedError("This method is not yet implemented for database storage mode")

    @override
    def save_constraint_equal_term_matrix(self, constraint_id: str, series_id: str) -> None:
        raise NotImplementedError("This method is not yet implemented for database storage mode")

    @override
    def delete_constraints(self, constraints: list[BindingConstraint]) -> None:
        raise NotImplementedError("This method is not yet implemented for database storage mode")

    @override
    def get_all_constraints(self) -> dict[str, BindingConstraint]:
        raise NotImplementedError("This method is not yet implemented for database storage mode")

    @override
    def get_constraint(self, constraint_id: str) -> BindingConstraint:
        raise NotImplementedError("This method is not yet implemented for database storage mode")

    @override
    def get_constraint_values_matrix(self, constraint_id: str) -> pl.DataFrame:
        raise NotImplementedError("This method is not yet implemented for database storage mode")

    @override
    def get_constraint_less_term_matrix(self, constraint_id: str) -> pl.DataFrame:
        raise NotImplementedError("This method is not yet implemented for database storage mode")

    @override
    def get_constraint_greater_term_matrix(self, constraint_id: str) -> pl.DataFrame:
        raise NotImplementedError("This method is not yet implemented for database storage mode")

    @override
    def get_constraint_equal_term_matrix(self, constraint_id: str) -> pl.DataFrame:
        raise NotImplementedError("This method is not yet implemented for database storage mode")

    @override
    def save_st_storage(self, area_id: str, st_storage: STStorage) -> None:
        raise NotImplementedError("This method is not yet implemented for database storage mode")

    @override
    def save_st_storages(self, area_id: str, storages: Sequence[STStorage]) -> None:
        raise NotImplementedError("This method is not yet implemented for database storage mode")

    @override
    def save_st_storage_pmax_injection(self, area_id: str, storage_id: str, series_id: str) -> None:
        raise NotImplementedError("This method is not yet implemented for database storage mode")

    @override
    def save_st_storage_pmax_withdrawal(self, area_id: str, storage_id: str, series_id: str) -> None:
        raise NotImplementedError("This method is not yet implemented for database storage mode")

    @override
    def save_st_storage_lower_rule_curve(self, area_id: str, storage_id: str, series_id: str) -> None:
        raise NotImplementedError("This method is not yet implemented for database storage mode")

    @override
    def save_st_storage_upper_rule_curve(self, area_id: str, storage_id: str, series_id: str) -> None:
        raise NotImplementedError("This method is not yet implemented for database storage mode")

    @override
    def save_st_storage_inflows(self, area_id: str, storage_id: str, series_id: str) -> None:
        raise NotImplementedError("This method is not yet implemented for database storage mode")

    @override
    def save_st_storage_cost_injection(self, area_id: str, storage_id: str, series_id: str) -> None:
        raise NotImplementedError("This method is not yet implemented for database storage mode")

    @override
    def save_st_storage_cost_withdrawal(self, area_id: str, storage_id: str, series_id: str) -> None:
        raise NotImplementedError("This method is not yet implemented for database storage mode")

    @override
    def save_st_storage_cost_level(self, area_id: str, storage_id: str, series_id: str) -> None:
        raise NotImplementedError("This method is not yet implemented for database storage mode")

    @override
    def save_st_storage_cost_variation_injection(self, area_id: str, storage_id: str, series_id: str) -> None:
        raise NotImplementedError("This method is not yet implemented for database storage mode")

    @override
    def save_st_storage_cost_variation_withdrawal(self, area_id: str, storage_id: str, series_id: str) -> None:
        raise NotImplementedError("This method is not yet implemented for database storage mode")

    @override
    def delete_st_storage(self, area_id: str, storage: STStorage) -> None:
        raise NotImplementedError("This method is not yet implemented for database storage mode")

    @override
    def delete_st_storage_additional_constraints(self, area_id: str, storage_id: str, constraints: list[str]) -> None:
        raise NotImplementedError("This method is not yet implemented for database storage mode")

    @override
    def save_st_storage_constraint_matrix(
        self, area_id: str, storage_id: str, constraint_id: str, series_id: str
    ) -> None:
        raise NotImplementedError("This method is not yet implemented for database storage mode")

    @override
    def save_st_storage_additional_constraints(
        self, area_id: str, storage_id: str, constraints: list[STStorageAdditionalConstraint]
    ) -> None:
        raise NotImplementedError("This method is not yet implemented for database storage mode")

    @override
    def get_all_st_storages(self) -> dict[str, dict[str, STStorage]]:
        raise NotImplementedError("This method is not yet implemented for database storage mode")

    @override
    def get_all_st_storages_for_area(self, area_id: str) -> Sequence[STStorage]:
        raise NotImplementedError("This method is not yet implemented for database storage mode")

    @override
    def get_st_storage(self, area_id: str, storage_id: str) -> STStorage:
        raise NotImplementedError("This method is not yet implemented for database storage mode")

    @override
    def st_storage_exists(self, area_id: str, storage_id: str) -> bool:
        raise NotImplementedError("This method is not yet implemented for database storage mode")

    @override
    def get_st_storage_pmax_injection(self, area_id: str, storage_id: str) -> pl.DataFrame:
        raise NotImplementedError("This method is not yet implemented for database storage mode")

    @override
    def get_st_storage_pmax_withdrawal(self, area_id: str, storage_id: str) -> pl.DataFrame:
        raise NotImplementedError("This method is not yet implemented for database storage mode")

    @override
    def get_st_storage_lower_rule_curve(self, area_id: str, storage_id: str) -> pl.DataFrame:
        raise NotImplementedError("This method is not yet implemented for database storage mode")

    @override
    def get_st_storage_upper_rule_curve(self, area_id: str, storage_id: str) -> pl.DataFrame:
        raise NotImplementedError("This method is not yet implemented for database storage mode")

    @override
    def get_st_storage_inflows(self, area_id: str, storage_id: str) -> pl.DataFrame:
        raise NotImplementedError("This method is not yet implemented for database storage mode")

    @override
    def get_st_storage_cost_injection(self, area_id: str, storage_id: str) -> pl.DataFrame:
        raise NotImplementedError("This method is not yet implemented for database storage mode")

    @override
    def get_st_storage_cost_withdrawal(self, area_id: str, storage_id: str) -> pl.DataFrame:
        raise NotImplementedError("This method is not yet implemented for database storage mode")

    @override
    def get_st_storage_cost_level(self, area_id: str, storage_id: str) -> pl.DataFrame:
        raise NotImplementedError("This method is not yet implemented for database storage mode")

    @override
    def get_st_storage_cost_variation_injection(self, area_id: str, storage_id: str) -> pl.DataFrame:
        raise NotImplementedError("This method is not yet implemented for database storage mode")

    @override
    def get_st_storage_cost_variation_withdrawal(self, area_id: str, storage_id: str) -> pl.DataFrame:
        raise NotImplementedError("This method is not yet implemented for database storage mode")

    @override
    def get_all_st_storage_additional_constraints(self) -> STStorageAdditionalConstraintsMap:
        raise NotImplementedError("This method is not yet implemented for database storage mode")

    @override
    def get_st_storage_additional_constraints(
        self, area_id: str, storage_id: str
    ) -> list[STStorageAdditionalConstraint]:
        raise NotImplementedError("This method is not yet implemented for database storage mode")

    @override
    def save_hydro_management(self, hydro_management: HydroManagement, area_id: str) -> None:
        raise NotImplementedError("This method is not yet implemented for database storage mode")

    @override
    def save_inflow_structure(self, inflow_structure: InflowStructure, area_id: str) -> None:
        raise NotImplementedError("This method is not yet implemented for database storage mode")

    @override
    def save_hydro_allocation(self, area_id: str, allocation: HydroAllocation) -> None:
        raise NotImplementedError("This method is not yet implemented for database storage mode")

    @override
    def save_hydro_correlation(self, area_id: str, correlation: HydroCorrelation) -> None:
        raise NotImplementedError("This method is not yet implemented for database storage mode")

    @override
    def get_all_hydro_properties(self) -> Dict[str, HydroProperties]:
        raise NotImplementedError("This method is not yet implemented for database storage mode")

    @override
    def get_hydro_management(self, area_id: str) -> HydroManagement:
        raise NotImplementedError("This method is not yet implemented for database storage mode")

    @override
    def get_inflow_structure(self, area_id: str) -> InflowStructure:
        raise NotImplementedError("This method is not yet implemented for database storage mode")

    @override
    def get_hydro_allocation(self, area_id: str) -> HydroAllocation:
        raise NotImplementedError("This method is not yet implemented for database storage mode")

    @override
    def get_hydro_allocation_matrix(self) -> dict[str, HydroAllocation]:
        raise NotImplementedError("This method is not yet implemented for database storage mode")

    @override
    def get_hydro_correlation(self, area_id: str) -> HydroCorrelation:
        raise NotImplementedError("This method is not yet implemented for database storage mode")

    @override
    def get_hydro_correlation_matrix(self) -> HydroCorrelationMatrix:
        raise NotImplementedError("This method is not yet implemented for database storage mode")

    @override
    def save_general_config(self, config: GeneralConfig) -> None:
        raise NotImplementedError("This method is not yet implemented for database storage mode")

    @override
    def get_general_config(self) -> GeneralConfig:
        raise NotImplementedError("This method is not yet implemented for database storage mode")

    @override
    def save_optimization_preferences(self, config: OptimizationPreferences) -> None:
        raise NotImplementedError("This method is not yet implemented for database storage mode")

    @override
    def get_optimization_preferences(self) -> OptimizationPreferences:
        raise NotImplementedError("This method is not yet implemented for database storage mode")

    @override
    def save_advanced_parameters(self, parameters: AdvancedParameters) -> None:
        raise NotImplementedError("This method is not yet implemented for database storage mode")

    @override
    def get_advanced_parameters(self) -> AdvancedParameters:
        raise NotImplementedError("This method is not yet implemented for database storage mode")

    @override
    def save_xpansion_candidate(self, candidate: XpansionCandidate, old_id: Optional[str] = None) -> None:
        raise NotImplementedError("This method is not yet implemented for database storage mode")

    @override
    def delete_xpansion_candidate(self, candidate_name: str) -> None:
        raise NotImplementedError("This method is not yet implemented for database storage mode")

    @override
    def save_xpansion_settings(self, settings: XpansionSettings) -> None:
        raise NotImplementedError("This method is not yet implemented for database storage mode")

    @override
    def create_xpansion_configuration(self) -> None:
        raise NotImplementedError("This method is not yet implemented for database storage mode")

    @override
    def delete_xpansion_configuration(self) -> None:
        raise NotImplementedError("This method is not yet implemented for database storage mode")

    @override
    def delete_xpansion_resource(self, resource_type: XpansionResourceFileType, filename: str) -> None:
        raise NotImplementedError("This method is not yet implemented for database storage mode")

    @override
    def save_xpansion_constraint(self, filename: str, content: bytes) -> None:
        raise NotImplementedError("This method is not yet implemented for database storage mode")

    @override
    def save_xpansion_capacity(self, filename: str, series: str) -> None:
        raise NotImplementedError("This method is not yet implemented for database storage mode")

    @override
    def save_xpansion_weight(self, filename: str, series: str) -> None:
        raise NotImplementedError("This method is not yet implemented for database storage mode")

    @override
    def save_xpansion_adequacy_criterion(self, criterion: XpansionAdequacyCriterion) -> None:
        raise NotImplementedError("This method is not yet implemented for database storage mode")

    @override
    def get_all_xpansion_candidates(self) -> list[XpansionCandidate]:
        raise NotImplementedError("This method is not yet implemented for database storage mode")

    @override
    def get_xpansion_candidate(self, candidate_id: str) -> XpansionCandidate:
        raise NotImplementedError("This method is not yet implemented for database storage mode")

    @override
    def checks_xpansion_candidate_coherence(self, candidate: XpansionCandidate) -> None:
        raise NotImplementedError("This method is not yet implemented for database storage mode")

    @override
    def checks_xpansion_candidate_can_be_deleted(self, candidate_name: str) -> None:
        raise NotImplementedError("This method is not yet implemented for database storage mode")

    @override
    def get_xpansion_settings(self) -> XpansionSettings:
        raise NotImplementedError("This method is not yet implemented for database storage mode")

    @override
    def checks_xpansion_settings_are_correct(self, settings: XpansionSettingsUpdate) -> None:
        raise NotImplementedError("This method is not yet implemented for database storage mode")

    @override
    def get_xpansion_resource(self, resource_type: XpansionResourceFileType, filename: str) -> bytes | pl.DataFrame:
        raise NotImplementedError("This method is not yet implemented for database storage mode")

    @override
    def get_xpansion_resources(self, resource_type: XpansionResourceFileType) -> list[str]:
        raise NotImplementedError("This method is not yet implemented for database storage mode")

    @override
    def checks_xpansion_resource_can_be_deleted(self, resource_type: XpansionResourceFileType, filename: str) -> None:
        raise NotImplementedError("This method is not yet implemented for database storage mode")

    @override
    def get_xpansion_adequacy_criterion(self) -> XpansionAdequacyCriterion:
        raise NotImplementedError("This method is not yet implemented for database storage mode")

    @override
    def save_thematic_trimming(self, trimming: ThematicTrimming) -> None:
        raise NotImplementedError("This method is not yet implemented for database storage mode")

    @override
    def get_thematic_trimming(self) -> ThematicTrimming:
        raise NotImplementedError("This method is not yet implemented for database storage mode")

    @override
    def save_adequacy_patch_parameters(self, parameters: AdequacyPatchParameters) -> None:
        raise NotImplementedError("This method is not yet implemented for database storage mode")

    @override
    def get_adequacy_patch_parameters(self) -> AdequacyPatchParameters:
        raise NotImplementedError("This method is not yet implemented for database storage mode")

    @override
    def save_timeseries_config(self, config: TimeSeriesConfiguration) -> None:
        raise NotImplementedError("This method is not yet implemented for database storage mode")

    @override
    def get_timeseries_config(self) -> TimeSeriesConfiguration:
        raise NotImplementedError("This method is not yet implemented for database storage mode")

    @override
    def save_district(self, district: District) -> None:
        raise NotImplementedError("This method is not yet implemented for database storage mode")

    @override
    def remove_district(self, district_id: str) -> None:
        raise NotImplementedError("This method is not yet implemented for database storage mode")

    @override
    def get_districts(self) -> Sequence[District]:
        raise NotImplementedError("This method is not yet implemented for database storage mode")

    @override
    def get_district(self, district_id: str) -> District:
        raise NotImplementedError("This method is not yet implemented for database storage mode")

    @override
    def district_exists(self, district_id: str) -> bool:
        raise NotImplementedError("This method is not yet implemented for database storage mode")

    @override
    def tmp_get_all_areas(self) -> list[str]:
        raise NotImplementedError("This method is not yet implemented for database storage mode")

    @override
    def get_invalid_areas_in_district(self, areas: list[str]) -> list[str]:
        raise NotImplementedError("This method is not yet implemented for database storage mode")

    @override
    def save_layer(self, layer: Layer) -> None:
        raise NotImplementedError("This method is not yet implemented for database storage mode")

    @override
    def delete_layer(self, layer: Layer) -> None:
        raise NotImplementedError("This method is not yet implemented for database storage mode")

    @override
    def get_layers(self) -> Sequence[Layer]:
        raise NotImplementedError("This method is not yet implemented for database storage mode")

    @override
    def layer_exists(self, layer_id: str) -> bool:
        raise NotImplementedError("This method is not yet implemented for database storage mode")

    @override
    def save_playlist_config(self, playlist: Playlist) -> None:
        raise NotImplementedError("This method is not yet implemented for database storage mode")

    @override
    def get_playlist_config(self) -> Playlist:
        raise NotImplementedError("This method is not yet implemented for database storage mode")

    @override
    def save_user_resource(self, resource_data: UserResourceDataCreation) -> None:
        raise NotImplementedError("This method is not yet implemented for database storage mode")

    @override
    def delete_user_resource(self, resource_path: PurePosixPath) -> None:
        raise NotImplementedError("This method is not yet implemented for database storage mode")

    @override
    def save_scenario_builder(self, rulesets: Rulesets) -> None:
        raise NotImplementedError("This method is not yet implemented for database storage mode")

    @override
    def get_rulesets(self) -> Rulesets:
        raise NotImplementedError("This method is not yet implemented for database storage mode")

    @override
    def get_active_ruleset_name(self, default_ruleset: str = "Default Ruleset") -> str:
        raise NotImplementedError("This method is not yet implemented for database storage mode")

    @override
    def get_scenario_by_type(self, scenario_type: ScenarioType) -> AnyScenarios:
        raise NotImplementedError("This method is not yet implemented for database storage mode")

    # Hydro series methods
    @override
    def get_hydro_credit_modulations(self, area_id: str) -> pl.DataFrame:
        raise NotImplementedError("This method is not yet implemented for database storage mode")

    @override
    def get_hydro_energy(self, area_id: str) -> pl.DataFrame:
        raise NotImplementedError("This method is not yet implemented for database storage mode")

    @override
    def get_hydro_inflow_pattern(self, area_id: str) -> pl.DataFrame:
        raise NotImplementedError("This method is not yet implemented for database storage mode")

    @override
    def get_hydro_maxpower(self, area_id: str) -> pl.DataFrame:
        raise NotImplementedError("This method is not yet implemented for database storage mode")

    @override
    def get_hydro_mingen(self, area_id: str) -> pl.DataFrame:
        raise NotImplementedError("This method is not yet implemented for database storage mode")

    @override
    def get_hydro_modulation(self, area_id: str) -> pl.DataFrame:
        raise NotImplementedError("This method is not yet implemented for database storage mode")

    @override
    def get_hydro_reservoir(self, area_id: str) -> pl.DataFrame:
        raise NotImplementedError("This method is not yet implemented for database storage mode")

    @override
    def get_hydro_run_of_river(self, area_id: str) -> pl.DataFrame:
        raise NotImplementedError("This method is not yet implemented for database storage mode")

    @override
    def get_hydro_water_values(self, area_id: str) -> pl.DataFrame:
        raise NotImplementedError("This method is not yet implemented for database storage mode")

    @override
    def save_hydro_credit_modulations(self, area_id: str, series_id: str) -> None:
        raise NotImplementedError("This method is not yet implemented for database storage mode")

    @override
    def save_hydro_energy(self, area_id: str, series_id: str) -> None:
        raise NotImplementedError("This method is not yet implemented for database storage mode")

    @override
    def save_hydro_inflow_pattern(self, area_id: str, series_id: str) -> None:
        raise NotImplementedError("This method is not yet implemented for database storage mode")

    @override
    def save_hydro_maxpower(self, area_id: str, series_id: str) -> None:
        raise NotImplementedError("This method is not yet implemented for database storage mode")

    @override
    def save_hydro_mingen(self, area_id: str, series_id: str) -> None:
        raise NotImplementedError("This method is not yet implemented for database storage mode")

    @override
    def save_hydro_modulation(self, area_id: str, series_id: str) -> None:
        raise NotImplementedError("This method is not yet implemented for database storage mode")

    @override
    def save_hydro_reservoir(self, area_id: str, series_id: str) -> None:
        raise NotImplementedError("This method is not yet implemented for database storage mode")

    @override
    def save_hydro_run_of_river(self, area_id: str, series_id: str) -> None:
        raise NotImplementedError("This method is not yet implemented for database storage mode")

    @override
    def save_hydro_water_values(self, area_id: str, series_id: str) -> None:
        raise NotImplementedError("This method is not yet implemented for database storage mode")

    # Link series methods
    @override
    def get_link_direct_capacities(self, area_from: str, area_to: str) -> pl.DataFrame:
        raise NotImplementedError("This method is not yet implemented for database storage mode")

    @override
    def get_link_indirect_capacities(self, area_from: str, area_to: str) -> pl.DataFrame:
        raise NotImplementedError("This method is not yet implemented for database storage mode")

    @override
    def get_link_series(self, area_from: str, area_to: str) -> pl.DataFrame:
        raise NotImplementedError("This method is not yet implemented for database storage mode")

    # User resources
    @override
    def get_all_user_resources(self) -> Iterator[UserResourceDataCreation]:
        raise NotImplementedError("This method is not yet implemented for database storage mode")
