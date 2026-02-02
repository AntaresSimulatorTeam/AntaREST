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
from typing import TYPE_CHECKING

from sqlalchemy.orm import Session
from typing_extensions import override

from antarest.study.business.model.config.adequacy_patch_model import AdequacyPatchParameters
from antarest.study.business.model.config.advanced_parameters_model import AdvancedParameters
from antarest.study.business.model.config.compatibility_parameters_model import CompatibilityParameters
from antarest.study.business.model.config.general_model import GeneralConfig
from antarest.study.business.model.config.optimization_config_model import OptimizationPreferences
from antarest.study.business.model.config.playlist_model import Playlist
from antarest.study.business.model.config.timeseries_config_model import TimeSeriesConfiguration
from antarest.study.dao.api.adequacy_patch_parameters_dao import AdequacyPatchParametersDao
from antarest.study.dao.api.advanced_parameters_dao import AdvancedParametersDao
from antarest.study.dao.api.compatibility_parameters_dao import CompatibilityParametersDao
from antarest.study.dao.api.general_config_dao import GeneralConfigDao
from antarest.study.dao.api.optimization_preferences_dao import OptimizationPreferencesDao
from antarest.study.dao.api.playlist_config_dao import PlaylistConfigDao
from antarest.study.dao.api.timeseries_config_dao import TimeSeriesConfigDao

if TYPE_CHECKING:
    from antarest.study.dao.database.database_study_dao import DatabaseStudyDao


class DatabaseStudySettingsDao(
    GeneralConfigDao,
    OptimizationPreferencesDao,
    AdvancedParametersDao,
    CompatibilityParametersDao,
    AdequacyPatchParametersDao,
    TimeSeriesConfigDao,
    PlaylistConfigDao,
):
    """Database implementation of all study settings DAOs"""

    def __init__(self, study_id: str, db_session: Session) -> None:
        self._study_id = study_id
        self._db_session = db_session

    def get_study_id(self) -> str:
        """Get the study ID for database queries."""
        return self._study_id

    def get_session(self) -> Session:
        """Get the SQLAlchemy session for database operations."""
        return self._db_session

    @abstractmethod
    def get_impl(self) -> "DatabaseStudyDao":
        pass

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
    def get_compatibility_parameters(self) -> CompatibilityParameters:
        raise NotImplementedError("This method is not yet implemented for database storage mode")

    @override
    def save_compatibility_parameters(self, parameters: CompatibilityParameters) -> None:
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
    def save_playlist_config(self, playlist: Playlist) -> None:
        raise NotImplementedError("This method is not yet implemented for database storage mode")

    @override
    def get_playlist_config(self) -> Playlist:
        raise NotImplementedError("This method is not yet implemented for database storage mode")
