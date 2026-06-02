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
from sqlalchemy.orm import Session
from typing_extensions import override

from antarest.core.utils.fastapi_sqlalchemy import db
from antarest.matrixstore.service import ISimpleMatrixService
from antarest.study.business.model.area_model import DEFAULT_LAYER_ID, DEFAULT_LAYER_NAME
from antarest.study.business.model.config.adequacy_patch_model import (
    AdequacyPatchParameters,
    initialize_adequacy_patch_parameters,
)
from antarest.study.business.model.config.advanced_parameters_model import (
    AdvancedParameters,
    initialize_advanced_parameters_against_version,
)
from antarest.study.business.model.config.compatibility_parameters_model import CompatibilityParameters
from antarest.study.business.model.config.general_model import GeneralConfig, initialize_general_config_against_version
from antarest.study.business.model.config.optimization_config_model import (
    OptimizationPreferences,
    initialize_optimization_preferences_against_version,
)
from antarest.study.business.model.config.playlist_model import Playlist
from antarest.study.business.model.config.timeseries_config_model import TimeSeriesConfiguration
from antarest.study.business.model.layer_model import Layer
from antarest.study.business.model.thematic_trimming_model import (
    ThematicTrimming,
    initialize_thematic_trimming_against_version,
)
from antarest.study.dao.api.study_factory_dao import StudyFactoryDao
from antarest.study.dao.database.database_study_dao import DatabaseStudyDao
from antarest.study.dao.database.models import STUDY_DATA_TABLE
from antarest.study.dao.database.sql_utils import upsert_one
from antarest.study.model import STUDY_VERSION_8_3, STUDY_VERSION_9_2
from antarest.study.storage.utils import StudyMetadataCreation
from antarest.study.storage.variantstudy.business.matrix_constants_generator import GeneratorMatrixConstants


def _create_default_settings(dao: DatabaseStudyDao, study_version: StudyVersion) -> None:
    """Saves default settings at study creation. Modifies the `dao` parameter in place"""
    general_config = GeneralConfig()
    initialize_general_config_against_version(general_config, study_version)
    dao.save_general_config(general_config)

    dao.save_playlist_config(Playlist())

    dao.save_timeseries_config(TimeSeriesConfiguration())

    advanced_parameters = AdvancedParameters()
    initialize_advanced_parameters_against_version(advanced_parameters, study_version)
    dao.save_advanced_parameters(advanced_parameters)

    optimization_preferences = OptimizationPreferences()
    initialize_optimization_preferences_against_version(optimization_preferences, study_version)
    dao.save_optimization_preferences(optimization_preferences)

    thematic_trimming = ThematicTrimming()
    initialize_thematic_trimming_against_version(thematic_trimming, study_version)
    dao.save_thematic_trimming(thematic_trimming)

    if study_version >= STUDY_VERSION_8_3:
        adequacy_patch_parameters = AdequacyPatchParameters()
        initialize_adequacy_patch_parameters(adequacy_patch_parameters, study_version)
        dao.save_adequacy_patch_parameters(adequacy_patch_parameters)

    if study_version >= STUDY_VERSION_9_2:
        dao.save_compatibility_parameters(CompatibilityParameters())


class DatabaseStudyDaoFactory(StudyFactoryDao):
    """
    Used to initialize a study inside DB
    """

    def __init__(
        self,
        matrix_service: ISimpleMatrixService,
        generator_matrix_constants: GeneratorMatrixConstants,
        session: Session | None = None,
    ) -> None:
        self._matrix_service = matrix_service
        self._generator_matrix_constants = generator_matrix_constants
        self._session = session

    @property
    def session(self) -> Session:
        """Get the SqlAlchemy session or create a new one on the fly if not available in the current thread."""
        if self._session is None:
            return db.session
        return self._session

    def _initialize_study_data_table(self, study_id: str) -> None:
        """
        Initialize the study data table as every DB DAO table is linked to it via foreign keys.
        """
        session = self.session
        upsert_one(session, STUDY_DATA_TABLE, {"study_id": study_id, "study_data_id": study_id})
        session.commit()

    @override
    def create_study_dao(self, metadata: StudyMetadataCreation) -> DatabaseStudyDao:
        dao = self.get_study_dao(metadata.id, metadata.managed)
        self._initialize_study_data_table(dao.get_study_id())
        dao.save_layer(Layer(id=DEFAULT_LAYER_ID, name=DEFAULT_LAYER_NAME))
        _create_default_settings(dao, metadata.version)
        return dao

    @override
    def get_study_dao(self, study_id: str, is_study_managed: bool) -> DatabaseStudyDao:
        return DatabaseStudyDao(study_id, self.session, self._matrix_service, self._generator_matrix_constants)
