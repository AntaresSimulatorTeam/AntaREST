# Copyright (c) 2024, RTE (https://www.rte-france.com)
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

from antarest.study.storage.study_upgrader import StudyUpgrader
from tests.storage.business.test_study_version_upgrader import are_same_dir
from tests.storage.study_upgrader.conftest import StudyAssets


def test_nominal_case(study_assets: StudyAssets):
    """
    Check that binding constraints and thermal folders are correctly modified
    """

    # upgrade the study
    study_upgrader = StudyUpgrader(study_assets.study_dir, "870")
    study_upgrader.upgrade()

    # compare input folders (bindings + thermals)
    actual_input_path = study_assets.study_dir.joinpath("input")
    expected_input_path = study_assets.expected_dir.joinpath("input")
    assert are_same_dir(actual_input_path, expected_input_path)


def test_empty_binding_constraints(study_assets: StudyAssets):
    """
    Check that binding constraints and thermal folders are correctly modified
    """

    # upgrade the study
    study_upgrader = StudyUpgrader(study_assets.study_dir, "870")
    study_upgrader.upgrade()

    # compare input folders (bindings + thermals)
    actual_input_path = study_assets.study_dir.joinpath("input")
    expected_input_path = study_assets.expected_dir.joinpath("input")
    assert are_same_dir(actual_input_path, expected_input_path)
