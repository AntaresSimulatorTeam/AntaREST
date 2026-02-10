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
from antarest.study.dao.database.models.settings import (
    ADVANCED_PARAMETERS_TABLE,
    COMPATIBILITY_PARAMETERS_TABLE,
    GENERAL_CONFIG_TABLE,
    OPTIMIZATION_PREFERENCES_TABLE,
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
        values = dict(
            study_id=self.get_study_id(),
            mode=config.mode,
            first_day=config.first_day,
            last_day=config.last_day,
            horizon=config.horizon,
            first_month=config.first_month,
            first_week_day=config.first_week_day,
            first_january=config.first_january,
            leap_year=config.leap_year,
            nb_years=config.nb_years,
            building_mode=config.building_mode,
            selection_mode=config.selection_mode,
            year_by_year=config.year_by_year,
            simulation_synthesis=config.simulation_synthesis,
            mc_scenario=config.mc_scenario,
            filtering=config.filtering,
            geographic_trimming=config.geographic_trimming,
            thematic_trimming=config.thematic_trimming,
        )
        session = self.get_session()
        upsert_one(session, GENERAL_CONFIG_TABLE, values)
        session.commit()

    @override
    def get_general_config(self) -> GeneralConfig:
        study_id = self._study_id
        stmt = select(GENERAL_CONFIG_TABLE).where((GENERAL_CONFIG_TABLE.c.study_id == study_id))
        row = self.get_session().execute(stmt).fetchone()
        if not row:
            raise StudyNotFoundError(study_id)
        return GeneralConfig(
            mode=row.mode,
            first_day=row.first_day,
            last_day=row.last_day,
            horizon=row.horizon,
            first_month=row.first_month,
            first_week_day=row.first_weekday,
            first_january=row.first_january,
            leap_year=row.leap_year,
            nb_years=row.nb_years,
            building_mode=row.building_mode,
            selection_mode=row.selection_mode,
            year_by_year=row.year_by_year,
            simulation_synthesis=row.simulation_synthesis,
            mc_scenario=row.mc_scenario,
            filtering=row.filtering,
            geographic_trimming=row.geographic_trimming,
            thematic_trimming=row.thematic_trimming,
        )

    @override
    def save_optimization_preferences(self, config: OptimizationPreferences) -> None:
        values = dict(
            study_id=self.get_study_id(),
            binding_constraints=config.binding_constraints,
            hurdle_costs=config.hurdle_costs,
            transmission_capacities=config.transmission_capacities,
            thermal_clusters_min_stable_power=config.thermal_clusters_min_stable_power,
            thermal_clusters_min_ud_time=config.thermal_clusters_min_ud_time,
            day_ahead_reserve=config.day_ahead_reserve,
            primary_reserve=config.primary_reserve,
            strategic_reserve=config.strategic_reserve,
            spinning_reserve=config.spinning_reserve,
            export_mps=config.export_mps,
            unfeasible_problem_behavior=config.unfeasible_problem_behavior,
            simplex_optimization_range=config.simplex_optimization_range,
        )
        session = self.get_session()
        upsert_one(session, OPTIMIZATION_PREFERENCES_TABLE, values)
        session.commit()

    @override
    def get_optimization_preferences(self) -> OptimizationPreferences:
        study_id = self._study_id
        stmt = select(OPTIMIZATION_PREFERENCES_TABLE).where((OPTIMIZATION_PREFERENCES_TABLE.c.study_id == study_id))
        row = self.get_session().execute(stmt).fetchone()
        if not row:
            raise StudyNotFoundError(study_id)
        return OptimizationPreferences(
            binding_constraints=row.binding_constraints,
            hurdle_costs=row.hurdle_costs,
            transmission_capacities=row.transmission_capacities,
            thermal_clusters_min_stable_power=row.thermal_clusters_min_stable_power,
            thermal_clusters_min_ud_time=row.thermal_clusters_min_ud_time,
            day_ahead_reserve=row.day_ahead_reserve,
            primary_reserve=row.primary_reserve,
            strategic_reserve=row.strategic_reserve,
            spinning_reserve=row.spinning_reserve,
            export_mps=row.export_mps,
            unfeasible_problem_behavior=row.unfeasible_problem_behavior,
            simplex_optimization_range=row.simplex_optimization_range,
        )

    @override
    def save_advanced_parameters(self, parameters: AdvancedParameters) -> None:
        values = dict(
            study_id=self.get_study_id(),
            accuracy_on_correlation=parameters.accuracy_on_correlation,
            power_fluctuations=parameters.power_fluctuations,
            shedding_policy=parameters.shedding_policy,
            hydro_pricing_mode=parameters.hydro_pricing_mode,
            hydro_heuristic_policy=parameters.hydro_heuristic_policy,
            unit_commitment_mode=parameters.unit_commitment_mode,
            number_of_cores_mode=parameters.number_of_cores_mode,
            day_ahead_reserve_management=parameters.day_ahead_reserve_management,
            renewable_generation_modelling=parameters.renewable_generation_modelling,
            seed_tsgen_wind=parameters.seed_tsgen_wind,
            seed_tsgen_load=parameters.seed_tsgen_load,
            seed_tsgen_hydro=parameters.seed_tsgen_hydro,
            seed_tsgen_thermal=parameters.seed_tsgen_thermal,
            seed_tsgen_solar=parameters.seed_tsgen_solar,
            seed_tsnumbers=parameters.seed_tsnumbers,
            seed_unsupplied_energy_costs=parameters.seed_unsupplied_energy_costs,
            seed_spilled_energy_costs=parameters.seed_spilled_energy_costs,
            seed_thermal_costs=parameters.seed_thermal_costs,
            seed_hydro_costs=parameters.seed_hydro_costs,
            seed_initial_reservoir_levels=parameters.seed_initial_reservoir_levels,
            initial_reservoir_levels=parameters.initial_reservoir_levels,
            accurate_shave_peaks_include_short_term_storage=parameters.accurate_shave_peaks_include_short_term_storage,
        )
        session = self.get_session()
        upsert_one(session, ADVANCED_PARAMETERS_TABLE, values)
        session.commit()

    @override
    def get_advanced_parameters(self) -> AdvancedParameters:
        study_id = self._study_id
        stmt = select(ADVANCED_PARAMETERS_TABLE).where((ADVANCED_PARAMETERS_TABLE.c.study_id == study_id))
        row = self.get_session().execute(stmt).fetchone()
        if not row:
            raise StudyNotFoundError(study_id)
        return AdvancedParameters(
            accuracy_on_correlation=row.accuracy_on_correlation,
            power_fluctuations=row.power_fluctuations,
            shedding_policy=row.shedding_policy,
            hydro_pricing_mode=row.hydro_pricing_mode,
            hydro_heuristic_policy=row.hydro_heuristic_policy,
            unit_commitment_mode=row.unit_commitment_mode,
            number_of_cores_mode=row.number_of_cores_mode,
            day_ahead_reserve_management=row.day_ahead_reserve_management,
            renewable_generation_modelling=row.renewable_generation_modelling,
            seed_tsgen_wind=row.seed_tsgen_wind,
            seed_tsgen_load=row.seed_tsgen_load,
            seed_tsgen_hydro=row.seed_tsgen_hydro,
            seed_tsgen_thermal=row.seed_tsgen_thermal,
            seed_tsgen_solar=row.seed_tsgen_solar,
            seed_tsnumbers=row.seed_tsnumbers,
            seed_unsupplied_energy_costs=row.seed_unsupplied_energy_costs,
            seed_spilled_energy_costs=row.seed_spilled_energy_costs,
            seed_thermal_costs=row.seed_thermal_costs,
            seed_hydro_costs=row.seed_hydro_costs,
            seed_initial_reservoir_levels=row.seed_initial_reservoir_levels,
            initial_reservoir_levels=row.initial_reservoir_levels,
            accurate_shave_peaks_include_short_term_storage=row.accurate_shave_peaks_include_short_term_storage,
        )

    @override
    def get_compatibility_parameters(self) -> CompatibilityParameters:
        study_id = self._study_id
        stmt = select(COMPATIBILITY_PARAMETERS_TABLE).where((COMPATIBILITY_PARAMETERS_TABLE.c.study_id == study_id))
        row = self.get_session().execute(stmt).fetchone()
        if not row:
            raise StudyNotFoundError(study_id)
        return CompatibilityParameters(hydro_pmax=row.hydro_pmax)

    @override
    def save_compatibility_parameters(self, parameters: CompatibilityParameters) -> None:
        values = dict(study_id=self.get_study_id(), hydro_pmax=parameters.hydro_pmax)
        session = self.get_session()
        upsert_one(session, COMPATIBILITY_PARAMETERS_TABLE, values)
        session.commit()

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
