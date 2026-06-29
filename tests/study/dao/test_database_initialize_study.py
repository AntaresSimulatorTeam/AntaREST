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
from typing import Callable

import pytest
from antares.study.version import StudyVersion

from antarest.study.business.model.config.adequacy_patch_model import (
    AdequacyPatchParameters,
    initialize_adequacy_patch_parameters,
)
from antarest.study.business.model.config.advanced_parameters_model import (
    AdvancedParameters,
    SheddingPolicy,
    initialize_advanced_parameters_against_version,
)
from antarest.study.business.model.config.compatibility_parameters_model import CompatibilityParameters
from antarest.study.business.model.config.general_model import GeneralConfig, initialize_general_config_against_version
from antarest.study.business.model.config.optimization_config_model import (
    OptimizationPreferences,
    TransmissionCapacities,
)
from antarest.study.business.model.config.playlist_model import Playlist, PlaylistValues
from antarest.study.business.model.config.timeseries_config_model import TimeSeriesConfiguration
from antarest.study.business.model.layer_model import Layer
from antarest.study.business.model.thematic_trimming_model import (
    ThematicTrimming,
    initialize_thematic_trimming_against_version,
)
from antarest.study.dao.api.study_dao import StudyDao
from antarest.study.model import (
    STUDY_REFERENCE_TEMPLATES,
    STUDY_VERSION_7_2,
    STUDY_VERSION_8_3,
    STUDY_VERSION_8_4,
    STUDY_VERSION_9_2,
)


@pytest.mark.parametrize("version", STUDY_REFERENCE_TEMPLATES)
def test_initialize_study(dao_builder: Callable[[StudyVersion], StudyDao], version: str) -> None:
    """Test that the study is initialized with the right default values"""
    study_version = StudyVersion.parse(version)
    dao = dao_builder(study_version)
    assert dao.get_layers() == [Layer(id="0", name="All", areas=[])]

    expected_general_config = GeneralConfig()
    initialize_general_config_against_version(expected_general_config, study_version)
    if study_version == STUDY_VERSION_7_2:
        expected_general_config.horizon = "0"

    expected_advanced_parameters = AdvancedParameters()
    initialize_advanced_parameters_against_version(expected_advanced_parameters, study_version)
    if study_version >= STUDY_VERSION_9_2:
        expected_advanced_parameters.shedding_policy = SheddingPolicy.ACCURATE_SHAVE_PEAKS

    expected_thematic_trimming = ThematicTrimming()
    initialize_thematic_trimming_against_version(expected_thematic_trimming, study_version)

    actual_general = dao.get_general_config()
    assert actual_general == expected_general_config

    actual_opt = dao.get_optimization_preferences()
    expected_opt = OptimizationPreferences()
    if study_version >= STUDY_VERSION_8_4:
        expected_opt.transmission_capacities = TransmissionCapacities.LOCAL_VALUES
    assert actual_opt == expected_opt

    actual_adv = dao.get_advanced_parameters()
    assert actual_adv == expected_advanced_parameters
    actual_playlist = dao.get_playlist_config()
    expected_playlist = Playlist(years={1: PlaylistValues()})
    assert actual_playlist == expected_playlist

    actual_ts = dao.get_timeseries_config()
    expected_ts = TimeSeriesConfiguration()
    assert actual_ts == expected_ts

    actual_tt = dao.get_thematic_trimming()
    assert actual_tt == expected_thematic_trimming

    if study_version >= STUDY_VERSION_8_3:
        expected_adequacy_patch_parameters = AdequacyPatchParameters()
        initialize_adequacy_patch_parameters(expected_adequacy_patch_parameters, study_version)
        actual_ap = dao.get_adequacy_patch_parameters()
        assert actual_ap == expected_adequacy_patch_parameters

    if study_version >= STUDY_VERSION_9_2:
        actual_cp = dao.get_compatibility_parameters()
        expected_cp = CompatibilityParameters()
        assert actual_cp == expected_cp
