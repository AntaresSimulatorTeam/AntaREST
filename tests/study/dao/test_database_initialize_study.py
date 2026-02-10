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
from antarest.study.business.model.config.adequacy_patch_model import AdequacyPatchParameters
from antarest.study.business.model.config.advanced_parameters_model import AdvancedParameters
from antarest.study.business.model.config.compatibility_parameters_model import CompatibilityParameters
from antarest.study.business.model.config.general_model import GeneralConfig
from antarest.study.business.model.config.optimization_config_model import OptimizationPreferences
from antarest.study.business.model.layer_model import Layer
from antarest.study.dao.database.database_study_dao import DatabaseStudyDao


def test_initialize_study(dao: DatabaseStudyDao) -> None:
    """Test that the study is initialized with the right default values"""
    assert dao.get_layers() == [Layer(id="0", name="All", areas=[])]
    assert dao.get_general_config() == GeneralConfig()
    assert dao.get_optimization_preferences() == OptimizationPreferences()
    assert dao.get_advanced_parameters() == AdvancedParameters()
    assert dao.get_adequacy_patch_parameters() == AdequacyPatchParameters()
    assert dao.get_compatibility_parameters() == CompatibilityParameters()
