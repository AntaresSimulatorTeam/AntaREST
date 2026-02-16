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

from typing import Optional, Self, Sequence

import polars as pl
from antares.study.version import StudyVersion
from sqlalchemy import select
from sqlalchemy.orm import Session
from typing_extensions import override

from antarest.matrixstore.service import ISimpleMatrixService
from antarest.study.business.model.binding_constraint_model import BindingConstraint
from antarest.study.business.model.renewable_cluster_model import RenewableCluster
from antarest.study.business.model.scenario_builder_model import AnyScenarios, Rulesets, ScenarioType
from antarest.study.business.model.sts_model import (
    STStorage,
    STStorageAdditionalConstraint,
    STStorageAdditionalConstraintsMap,
)
from antarest.study.business.model.thematic_trimming_model import ThematicTrimming
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
from antarest.study.dao.database.database_district_dao import DatabaseDistrictDao
from antarest.study.dao.database.database_hydro_dao import DatabaseHydroDao
from antarest.study.dao.database.database_layer_dao import DatabaseLayerDao
from antarest.study.dao.database.database_link_dao import DatabaseLinkDao
from antarest.study.dao.database.database_study_settings_dao import DatabaseStudySettingsDao
from antarest.study.dao.database.database_thermal_dao import DatabaseThermalDao
from antarest.study.dao.database.database_user_resources import DatabaseUserResourcesDao
from antarest.study.model import Study
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy


class DatabaseStudyDao(
    StudyDao,
    DatabaseAreaDao,
    DatabaseAreaPropertiesDao,
    DatabaseDistrictDao,
    DatabaseLinkDao,
    DatabaseLayerDao,
    DatabaseHydroDao,
    DatabaseThermalDao,
    DatabaseStudySettingsDao,
    DatabaseUserResourcesDao,
):
    """
    Database implementation of StudyDao.
    """

    def __init__(self, study_id: str, db_session: Session, matrix_service: ISimpleMatrixService) -> None:
        """
        Initialize DatabaseStudyDao.

        Args:
            study_id: The study ID for database queries
            db_session: SQLAlchemy session for database operations
        """
        DatabaseAreaDao.__init__(self, study_id, db_session)
        DatabaseAreaPropertiesDao.__init__(self, study_id, db_session)
        DatabaseDistrictDao.__init__(self, study_id, db_session)
        DatabaseLinkDao.__init__(self, study_id, db_session)
        DatabaseLayerDao.__init__(self, study_id, db_session)
        DatabaseHydroDao.__init__(self, study_id, db_session)
        DatabaseThermalDao.__init__(self, study_id, db_session)
        DatabaseStudySettingsDao.__init__(self, study_id, db_session)
        self._matrix_service = matrix_service

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

    def get_matrix(self, matrix_id: str) -> pl.DataFrame:
        return self._matrix_service.get(matrix_id)

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
