# Copyright (c) 2025, RTE (https://www.rte-france.com)
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

from typing import Any

import pytest
from antares.study.version import StudyVersion

from antarest.study.business.model.thematic_trimming_model import ThematicTrimming, initialize_thematic_trimming
from antarest.study.business.study_interface import FileStudyInterface
from antarest.study.business.thematic_trimming_management import ThematicTrimmingManager
from antarest.study.model import (
    STUDY_VERSION_7_0,
    STUDY_VERSION_8,
    STUDY_VERSION_8_2,
    STUDY_VERSION_8_3,
    STUDY_VERSION_8_4,
    STUDY_VERSION_8_6,
    STUDY_VERSION_9_1,
    STUDY_VERSION_9_3,
)
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.model.command_context import CommandContext


@pytest.mark.parametrize(
    ("version", "expected", "ini_content"),
    [
        pytest.param(STUDY_VERSION_7_0, ThematicTrimming(), {}, id="v7"),
        pytest.param(
            STUDY_VERSION_8,
            ThematicTrimming(avl_dtg=False),
            {"variables selection": {"select_var -": ["AVL DTG"]}},
            id="v8",
        ),
        pytest.param(
            STUDY_VERSION_8_2,
            ThematicTrimming(avl_dtg=False),
            {"variables selection": {"select_var -": ["AVL DTG"]}},
            id="v8.2",
        ),
        pytest.param(
            STUDY_VERSION_8_3,
            ThematicTrimming(dens=False, profit_by_plant=False),
            {"variables selection": {"selected_vars_reset": True, "select_var -": ["DENS", "Profit by plant"]}},
            id="v8.3",
        ),
        pytest.param(
            STUDY_VERSION_8_4,
            ThematicTrimming(cong_fee_alg=True),
            {"variables selection": {"selected_vars_reset": False, "select_var +": ["CONG. FEE (ALG.)"]}},
            id="v8.4",
        ),
        pytest.param(
            STUDY_VERSION_8_6,
            ThematicTrimming(sts_inj_by_plant=False),
            {"variables selection": {"selected_vars_reset": True, "select_var -": ["STS inj by plant"]}},
            id="v8.6",
        ),
        pytest.param(
            STUDY_VERSION_9_1,
            ThematicTrimming(sts_by_group=False),
            {"variables selection": {"selected_vars_reset": True, "select_var -": ["STS by group"]}},
            id="v9.1",
        ),
        pytest.param(
            STUDY_VERSION_9_3,
            ThematicTrimming(dispatch_gen=False, renewable_gen=False),
            {
                "variables selection": {
                    "selected_vars_reset": True,
                    "select_var -": ["RENEWABLE GEN.", "DISPATCH. GEN."],
                }
            },
            id="v9.3 -",
        ),
        pytest.param(
            STUDY_VERSION_9_3,
            ThematicTrimming(dispatch_gen=True, renewable_gen=True),
            {
                "variables selection": {
                    "selected_vars_reset": True,
                    "select_var +": ["RENEWABLE GEN.", "DISPATCH. GEN."],
                }
            },
            id="v9.3 +",
        ),
    ],
)
def test_thematic_trimming_config(
    command_context: CommandContext,
    empty_study_920: FileStudy,
    version: StudyVersion,
    expected: ThematicTrimming,
    ini_content: dict[str, Any],
) -> None:
    thematic_trimming_manager = ThematicTrimmingManager(
        command_context=command_context,
    )
    empty_study_920.config.version = version
    study = FileStudyInterface(empty_study_920)
    study.file_study.tree.save(ini_content, ["settings", "generaldata"])

    actual = thematic_trimming_manager.get_thematic_trimming(study)
    initialize_thematic_trimming(
        expected, version, ini_content.get("variables selection", {}).get("selected_vars_reset", True)
    )
    assert actual == expected
