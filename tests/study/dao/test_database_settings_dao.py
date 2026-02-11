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

from sqlalchemy.orm import Session

from antarest.matrixstore.service import ISimpleMatrixService
from antarest.study.business.model.config.adequacy_patch_model import AdequacyPatchParameters, PriceTakingOrder
from antarest.study.business.model.config.advanced_parameters_model import (
    AdvancedParameters,
    SheddingPolicy,
    UnitCommitmentMode,
)
from antarest.study.business.model.config.compatibility_parameters_model import CompatibilityParameters, HydroPmax
from antarest.study.business.model.config.general_model import GeneralConfig, Mode, Month
from antarest.study.business.model.config.optimization_config_model import (
    OptimizationPreferences,
)
from antarest.study.business.model.config.playlist_model import Playlist, PlaylistValues
from antarest.study.business.model.config.timeseries_config_model import TimeSeriesConfiguration, TimeSeriesType
from antarest.study.dao.database.database_study_dao import DatabaseStudyDao
from antarest.study.model import STUDY_VERSION_9_3
from tests.study.dao.conftest import build_dao


def test_nominal_case(dao: DatabaseStudyDao) -> None:
    # General Config
    new_general_config = GeneralConfig(first_month=Month.OCTOBER, geographic_trimming=True, mode=Mode.ADEQUACY)
    dao.save_general_config(new_general_config)
    assert dao.get_general_config() == new_general_config

    # Advanced Parameters
    new_parameters = AdvancedParameters(
        unit_commitment_mode=UnitCommitmentMode.MILP, shedding_policy=SheddingPolicy.MINIMIZE_DURATION
    )
    dao.save_advanced_parameters(new_parameters)
    assert dao.get_advanced_parameters() == new_parameters

    # AdequacyPatch Parameters
    params = AdequacyPatchParameters(enable_adequacy_patch=True, price_taking_order=PriceTakingOrder.LOAD)
    dao.save_adequacy_patch_parameters(params)
    assert dao.get_adequacy_patch_parameters() == params

    # TimeSeries Config
    timeseries = TimeSeriesConfiguration(thermal=TimeSeriesType(number=4))
    dao.save_timeseries_config(timeseries)
    assert dao.get_timeseries_config() == timeseries

    # Playlist Config
    playlist = Playlist(years={4: PlaylistValues(status=False, weight=0.2), 7: PlaylistValues(weight=1.1)})
    dao.save_playlist_config(playlist)
    assert dao.get_playlist_config() == playlist

    # Optimization preferences
    preferences = OptimizationPreferences(binding_constraints=False, export_mps="optim-1")
    dao.save_optimization_preferences(preferences)
    assert dao.get_optimization_preferences() == preferences


def test_compatibility_parameters(db_session: Session, matrix_service: ISimpleMatrixService) -> None:
    # Create a study in version 9.3 to test the compatibility parameters
    dao = build_dao(db_session, matrix_service, STUDY_VERSION_9_3)
    assert dao.get_compatibility_parameters() == CompatibilityParameters()
    new_parameters = CompatibilityParameters(hydro_pmax=HydroPmax.HOURLY)
    dao.save_compatibility_parameters(new_parameters)
    assert dao.get_compatibility_parameters() == new_parameters
