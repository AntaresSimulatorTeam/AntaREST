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

from sqlalchemy import select
from sqlalchemy.orm import Session
from typing_extensions import override

from antarest.core.exceptions import StudyNotFoundError
from antarest.core.serde.json import from_json, to_json_string
from antarest.study.business.model.config.adequacy_patch_model import AdequacyPatchParameters
from antarest.study.business.model.config.advanced_parameters_model import AdvancedParameters
from antarest.study.business.model.config.compatibility_parameters_model import (
    CompatibilityParameters,
    initialize_compatibility_parameters_against_version,
)
from antarest.study.business.model.config.general_model import GeneralConfig
from antarest.study.business.model.config.optimization_config_model import OptimizationPreferences
from antarest.study.business.model.config.playlist_model import Playlist
from antarest.study.business.model.config.timeseries_config_model import TimeSeriesConfiguration, TimeSeriesType
from antarest.study.dao.api.adequacy_patch_parameters_dao import AdequacyPatchParametersDao
from antarest.study.dao.api.advanced_parameters_dao import AdvancedParametersDao
from antarest.study.dao.api.compatibility_parameters_dao import CompatibilityParametersDao
from antarest.study.dao.api.general_config_dao import GeneralConfigDao
from antarest.study.dao.api.optimization_preferences_dao import OptimizationPreferencesDao
from antarest.study.dao.api.playlist_config_dao import PlaylistConfigDao
from antarest.study.dao.api.timeseries_config_dao import TimeSeriesConfigDao
from antarest.study.dao.database.common import get_row_representation_as_dict
from antarest.study.dao.database.models.settings import (
    ADEQUACY_PATCH_PARAMETERS_TABLE,
    ADVANCED_PARAMETERS_TABLE,
    COMPATIBILITY_PARAMETERS_TABLE,
    GENERAL_CONFIG_TABLE,
    OPTIMIZATION_PREFERENCES_TABLE,
    PLAYLIST_TABLE,
    TIMESERIES_CONFIG_TABLE,
)
from antarest.study.dao.database.sql_utils import upsert_one

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
        values = dict(study_id=self.get_study_id(), **config.model_dump(mode="json"))
        session = self.get_session()
        upsert_one(session, GENERAL_CONFIG_TABLE, values)
        session.commit()

    @override
    def get_general_config(self) -> GeneralConfig:
        study_id = self._study_id
        stmt = select(GENERAL_CONFIG_TABLE).where(GENERAL_CONFIG_TABLE.c.study_id == study_id)
        row = self.get_session().execute(stmt).fetchone()
        if not row:
            raise StudyNotFoundError(study_id)
        data = get_row_representation_as_dict(row)
        del data["study_id"]
        return GeneralConfig(**data)

    @override
    def save_optimization_preferences(self, config: OptimizationPreferences) -> None:
        values = dict(study_id=self.get_study_id(), **config.model_dump(exclude={"export_mps"}))
        # Handle `export_mps` differently as it can either be a string or a boolean but will be stored as String in DB.
        if isinstance(config.export_mps, bool):
            mps = str(config.export_mps)
        else:
            mps = config.export_mps
        values["export_mps"] = mps

        session = self.get_session()
        upsert_one(session, OPTIMIZATION_PREFERENCES_TABLE, values)
        session.commit()

    @override
    def get_optimization_preferences(self) -> OptimizationPreferences:
        study_id = self._study_id
        stmt = select(OPTIMIZATION_PREFERENCES_TABLE).where(OPTIMIZATION_PREFERENCES_TABLE.c.study_id == study_id)
        row = self.get_session().execute(stmt).fetchone()
        if not row:
            raise StudyNotFoundError(study_id)

        data = get_row_representation_as_dict(row)
        del data["study_id"]
        # Handle `export_mps` differently as it is stored as String in DB, but it can either be a string or a boolean.
        mps: bool | str
        if row.export_mps.lower() == "true":
            mps = True
        elif row.export_mps.lower() == "false":
            mps = False
        else:
            mps = row.export_mps
        data["export_mps"] = mps

        return OptimizationPreferences(**data)

    @override
    def save_advanced_parameters(self, parameters: AdvancedParameters) -> None:
        values = dict(study_id=self.get_study_id(), **parameters.model_dump())
        session = self.get_session()
        upsert_one(session, ADVANCED_PARAMETERS_TABLE, values)
        session.commit()

    @override
    def get_advanced_parameters(self) -> AdvancedParameters:
        study_id = self._study_id
        stmt = select(ADVANCED_PARAMETERS_TABLE).where(ADVANCED_PARAMETERS_TABLE.c.study_id == study_id)
        row = self.get_session().execute(stmt).fetchone()
        if not row:
            raise StudyNotFoundError(study_id)

        data = get_row_representation_as_dict(row)
        del data["study_id"]
        return AdvancedParameters(**data)

    @override
    def get_compatibility_parameters(self) -> CompatibilityParameters:
        study_id = self._study_id
        stmt = select(COMPATIBILITY_PARAMETERS_TABLE).where(COMPATIBILITY_PARAMETERS_TABLE.c.study_id == study_id)
        row = self.get_session().execute(stmt).fetchone()
        if not row:
            raise StudyNotFoundError(study_id)
        parameters = CompatibilityParameters(hydro_pmax=row.hydro_pmax, reserves_enabled=row.reserves_enabled)
        version = self.get_impl().get_version()
        initialize_compatibility_parameters_against_version(parameters, version)
        return parameters

    @override
    def save_compatibility_parameters(self, parameters: CompatibilityParameters) -> None:
        values = dict(
            study_id=self.get_study_id(), hydro_pmax=parameters.hydro_pmax, reserves_enabled=parameters.reserves_enabled
        )
        session = self.get_session()
        upsert_one(session, COMPATIBILITY_PARAMETERS_TABLE, values)
        session.commit()

    @override
    def save_adequacy_patch_parameters(self, parameters: AdequacyPatchParameters) -> None:
        values = dict(study_id=self.get_study_id(), **parameters.model_dump())
        session = self.get_session()
        upsert_one(session, ADEQUACY_PATCH_PARAMETERS_TABLE, values)
        session.commit()

    @override
    def get_adequacy_patch_parameters(self) -> AdequacyPatchParameters:
        study_id = self._study_id
        stmt = select(ADEQUACY_PATCH_PARAMETERS_TABLE).where(ADEQUACY_PATCH_PARAMETERS_TABLE.c.study_id == study_id)
        row = self.get_session().execute(stmt).fetchone()
        if not row:
            raise StudyNotFoundError(study_id)

        data = get_row_representation_as_dict(row)
        del data["study_id"]
        return AdequacyPatchParameters(**data)

    @override
    def save_timeseries_config(self, config: TimeSeriesConfiguration) -> None:
        values = dict(study_id=self.get_study_id(), thermal_number=config.thermal.number)
        session = self.get_session()
        upsert_one(session, TIMESERIES_CONFIG_TABLE, values)
        session.commit()

    @override
    def get_timeseries_config(self) -> TimeSeriesConfiguration:
        study_id = self._study_id
        stmt = select(TIMESERIES_CONFIG_TABLE).where(TIMESERIES_CONFIG_TABLE.c.study_id == study_id)
        row = self.get_session().execute(stmt).fetchone()
        if not row:
            raise StudyNotFoundError(study_id)
        return TimeSeriesConfiguration(thermal=TimeSeriesType(number=row.thermal_number))

    @override
    def save_playlist_config(self, playlist: Playlist) -> None:
        values = dict(study_id=self.get_study_id(), years=to_json_string(playlist.years))
        session = self.get_session()
        upsert_one(session, PLAYLIST_TABLE, values)
        session.commit()

    @override
    def get_playlist_config(self) -> Playlist:
        study_id = self._study_id
        stmt = select(PLAYLIST_TABLE).where(PLAYLIST_TABLE.c.study_id == study_id)
        row = self.get_session().execute(stmt).fetchone()
        if not row:
            raise StudyNotFoundError(study_id)
        return Playlist(years=from_json(row.years))
