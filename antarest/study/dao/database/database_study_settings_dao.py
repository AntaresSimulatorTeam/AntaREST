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
    CompatibilityParametersDao,
    GeneralConfigDao,
    AdvancedParametersDao,
    AdequacyPatchParametersDao,
    OptimizationPreferencesDao,
    PlaylistConfigDao,
    TimeSeriesConfigDao,
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
