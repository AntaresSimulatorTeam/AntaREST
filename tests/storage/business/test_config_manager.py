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

from antarest.study.business.model.thematic_trimming_model import (
    ThematicTrimming,
    get_thematic_trimming_fields_according_to_version,
)
from antarest.study.business.thematic_trimming_management import ThematicTrimmingManager
from antarest.study.model import (
    STUDY_VERSION_7_0,
    STUDY_VERSION_8,
    STUDY_VERSION_8_2,
    STUDY_VERSION_8_3,
    STUDY_VERSION_8_4,
    STUDY_VERSION_8_5,
    STUDY_VERSION_8_6,
    STUDY_VERSION_9_1,
    STUDY_VERSION_9_3,
)
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.model.command_context import CommandContext
from tests.helpers import file_study_interface


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
            ThematicTrimming(
                ov_cost=False,
                op_cost=False,
                mrg_price=False,
                co2_emis=False,
                dtg_by_plant=False,
                balance=False,
                row_bal=False,
                psp=False,
                misc_ndg=False,
                load=False,
                h_ror=False,
                wind=False,
                h_stor=False,
                h_pump=False,
                h_lev=False,
                h_infl=False,
                h_ovfl=False,
                h_val=False,
                h_cost=False,
                unsp_enrg=False,
                spil_enrg=False,
                lold=False,
                lolp=False,
                avl_dtg=False,
                dtg_mrg=False,
                max_mrg=False,
                np_cost=False,
                np_cost_by_plant=False,
                nodu=False,
                nodu_by_plant=False,
                flow_lin=False,
                ucap_lin=False,
                loop_flow=False,
                flow_quad=False,
                cong_fee_abs=False,
                marg_cost=False,
                cong_prob_plus=False,
                cong_prob_minus=False,
                hurdle_cost=False,
                cong_fee_alg=True,
            ),
            {"variables selection": {"selected_vars_reset": False, "select_var +": ["CONG. FEE (ALG.)"]}},
            id="v8.4",
        ),
        pytest.param(
            STUDY_VERSION_8_5,
            ThematicTrimming(lmr_viol=False),
            {"variables selection": {"selected_vars_reset": True, "select_var -": ["LMR VIOL."]}},
            id="v8.5",
        ),
        pytest.param(
            STUDY_VERSION_8_6,
            ThematicTrimming(sts_inj_by_plant=False, nox_emis=False),
            {"variables selection": {"selected_vars_reset": True, "select_var -": ["STS inj by plant", "NOX EMIS."]}},
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
    study = file_study_interface(empty_study_920)
    study.file_study.tree.save(ini_content, ["settings", "generaldata"])

    # Initalize the expected fields to avoid writing them all inside the test
    default_bool = ini_content.get("variables selection", {}).get("selected_vars_reset", True)
    for field in get_thematic_trimming_fields_according_to_version(version):
        if getattr(expected, field) is None:
            setattr(expected, field, default_bool)

    actual = thematic_trimming_manager.get_thematic_trimming(study)
    assert actual == expected
