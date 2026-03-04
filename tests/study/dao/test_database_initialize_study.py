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
import pytest
from antares.study.version import StudyVersion
from sqlalchemy.orm import Session
from study.dao.conftest import build_dao

from antarest.matrixstore.service import ISimpleMatrixService
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
from antarest.study.business.model.config.optimization_config_model import OptimizationPreferences
from antarest.study.business.model.config.playlist_model import Playlist
from antarest.study.business.model.config.timeseries_config_model import TimeSeriesConfiguration
from antarest.study.business.model.layer_model import Layer
from antarest.study.business.model.thematic_trimming_model import (
    ThematicTrimming,
    initialize_thematic_trimming_against_version,
)
from antarest.study.model import STUDY_REFERENCE_TEMPLATES, STUDY_VERSION_8_3, STUDY_VERSION_9_2


@pytest.mark.parametrize("version", STUDY_REFERENCE_TEMPLATES)
def test_initialize_study(db_session: Session, matrix_service: ISimpleMatrixService, version: str) -> None:
    """Test that the study is initialized with the right default values"""
    study_version = StudyVersion.parse(version)
    dao = build_dao(db_session, matrix_service, study_version)
    assert dao.get_layers() == [Layer(id="0", name="All", areas=[])]

    expected_general_config = GeneralConfig()
    initialize_general_config_against_version(expected_general_config, study_version)
    expected_advanced_parameters = AdvancedParameters()
    initialize_advanced_parameters_against_version(expected_advanced_parameters, study_version)
    expected_thematic_trimming = ThematicTrimming()
    initialize_thematic_trimming_against_version(expected_thematic_trimming, study_version)

    assert dao.get_general_config() == expected_general_config
    assert dao.get_optimization_preferences() == OptimizationPreferences()
    assert dao.get_advanced_parameters() == expected_advanced_parameters
    assert dao.get_playlist_config() == Playlist()
    assert dao.get_timeseries_config() == TimeSeriesConfiguration()
    assert dao.get_thematic_trimming() == expected_thematic_trimming

    if study_version >= STUDY_VERSION_8_3:
        expected_adequacy_patch_parameters = AdequacyPatchParameters()
        initialize_adequacy_patch_parameters(expected_adequacy_patch_parameters, study_version)
        assert dao.get_adequacy_patch_parameters() == expected_adequacy_patch_parameters

    if study_version >= STUDY_VERSION_9_2:
        assert dao.get_compatibility_parameters() == CompatibilityParameters()
