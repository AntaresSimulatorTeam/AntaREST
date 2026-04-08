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

from collections.abc import Sequence
from typing import Self

import polars as pl
from antares.study.version import StudyVersion
from sqlalchemy import select
from sqlalchemy.orm import Session
from typing_extensions import override

from antarest.matrixstore.service import ISimpleMatrixService
from antarest.study.business.model.binding_constraint_model import BindingConstraint
from antarest.study.dao.api.study_dao import StudyDao
from antarest.study.dao.database.database_area_dao import DatabaseAreaDao
from antarest.study.dao.database.database_area_properties_dao import DatabaseAreaPropertiesDao
from antarest.study.dao.database.database_district_dao import DatabaseDistrictDao
from antarest.study.dao.database.database_hydro_dao import DatabaseHydroDao
from antarest.study.dao.database.database_layer_dao import DatabaseLayerDao
from antarest.study.dao.database.database_link_dao import DatabaseLinkDao
from antarest.study.dao.database.database_renewable_dao import DatabaseRenewableDao
from antarest.study.dao.database.database_scenario_builder_dao import DatabaseScenarioBuilderDao
from antarest.study.dao.database.database_st_storage_dao import DatabaseStStorageDao
from antarest.study.dao.database.database_study_settings_dao import DatabaseStudySettingsDao
from antarest.study.dao.database.database_thematic_trimming_dao import DatabaseThematicTrimmingDao
from antarest.study.dao.database.database_thermal_dao import DatabaseThermalDao
from antarest.study.dao.database.database_user_resources import DatabaseUserResourcesDao
from antarest.study.dao.database.database_xpansion_dao import DatabaseXpansionDao
from antarest.study.dao.database.models.comments import COMMENTS_TABLE
from antarest.study.dao.database.sql_utils import upsert_one
from antarest.study.model import Study, StudyMetadataUpdate
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.business.matrix_constants_generator import GeneratorMatrixConstants


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
    DatabaseRenewableDao,
    DatabaseUserResourcesDao,
    DatabaseStStorageDao,
    DatabaseThematicTrimmingDao,
    DatabaseScenarioBuilderDao,
    DatabaseXpansionDao,
):
    """
    Database implementation of StudyDao.
    """

    def __init__(
        self,
        study_id: str,
        db_session: Session,
        matrix_service: ISimpleMatrixService,
        generator_matrix_constants: GeneratorMatrixConstants,
    ) -> None:
        """
        Initialize DatabaseStudyDao.

        Args:
            study_id: The study ID for database queries
            db_session: SQLAlchemy session for database operations
            matrix_service: Matrix storage service
            generator_matrix_constants: Predefined matrix constants generator
        """
        DatabaseAreaDao.__init__(self, study_id, db_session)
        DatabaseAreaPropertiesDao.__init__(self, study_id, db_session)
        DatabaseDistrictDao.__init__(self, study_id, db_session)
        DatabaseLinkDao.__init__(self, study_id, db_session)
        DatabaseLayerDao.__init__(self, study_id, db_session)
        DatabaseHydroDao.__init__(self, study_id, db_session)
        DatabaseThermalDao.__init__(self, study_id, db_session)
        DatabaseStudySettingsDao.__init__(self, study_id, db_session)
        DatabaseRenewableDao.__init__(self, study_id, db_session)
        DatabaseUserResourcesDao.__init__(self, study_id, db_session)
        DatabaseStStorageDao.__init__(self, study_id, db_session)
        DatabaseThematicTrimmingDao.__init__(self, study_id, db_session)
        DatabaseScenarioBuilderDao.__init__(self, study_id, db_session)
        DatabaseXpansionDao.__init__(self, study_id, db_session)
        self._matrix_service = matrix_service
        self._generator_matrix_constants = generator_matrix_constants

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
        stmt = select(COMMENTS_TABLE.c.comments).where(COMMENTS_TABLE.c.study_id == self._study_id)
        comments = self._db_session.execute(stmt).scalar_one_or_none()
        return comments if comments is not None else ""

    @override
    def save_comments(self, comments: str) -> None:
        upsert_one(self._db_session, COMMENTS_TABLE, {"study_id": self._study_id, "comments": comments})
        self._db_session.commit()

    @override
    def update_antares_file(self, metadata: StudyMetadataUpdate) -> None:
        pass

    @override
    def update_cache(self) -> None:
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
