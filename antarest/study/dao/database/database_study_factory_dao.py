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
from antarest.study.business.model.config.adequacy_patch_model import AdequacyPatchParameters
from antarest.study.business.model.config.advanced_parameters_model import AdvancedParameters
from antarest.study.business.model.config.compatibility_parameters_model import CompatibilityParameters
from antarest.study.business.model.config.general_model import GeneralConfig
from antarest.study.business.model.config.optimization_config_model import OptimizationPreferences
from antarest.study.business.model.config.playlist_model import Playlist
from antarest.study.business.model.config.timeseries_config_model import TimeSeriesConfiguration
from antarest.study.business.model.layer_model import Layer
from antarest.study.business.model.thematic_trimming_model import ThematicTrimming
from antarest.study.dao.api.study_factory_dao import StudyFactoryDao
from antarest.study.dao.database.database_study_dao import DatabaseStudyDao
from antarest.study.model import STUDY_VERSION_8_3, STUDY_VERSION_9_2, Study


class DatabaseStudyDaoFactory(StudyFactoryDao):
    """
    Used to initialize a study inside DB
    """

    def __init__(self, matrix_service: ISimpleMatrixService, session: Session | None = None) -> None:
        self._matrix_service = matrix_service
        self._session = session

    @property
    def session(self) -> Session:
        """Get the SqlAlchemy session or create a new one on the fly if not available in the current thread."""
        if self._session is None:
            return db.session
        return self._session

    @override
    def create_study_dao(self, study: Study) -> DatabaseStudyDao:
        dao = DatabaseStudyDao(study.id, self.session, self._matrix_service)
        dao.save_layer(Layer(id=DEFAULT_LAYER_ID, name=DEFAULT_LAYER_NAME))
        dao.save_general_config(GeneralConfig())
        dao.save_playlist_config(Playlist())
        dao.save_timeseries_config(TimeSeriesConfiguration())
        dao.save_advanced_parameters(AdvancedParameters())
        dao.save_optimization_preferences(OptimizationPreferences())
        dao.save_thematic_trimming(ThematicTrimming())
        study_version = StudyVersion.parse(study.version)
        if study_version > STUDY_VERSION_8_3:
            dao.save_adequacy_patch_parameters(AdequacyPatchParameters())
        if study_version > STUDY_VERSION_9_2:
            dao.save_compatibility_parameters(CompatibilityParameters())
        return dao
