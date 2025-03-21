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

from pathlib import Path
from unittest.mock import Mock

from antarest.study.business.study_interface import StudyInterface
from antarest.study.business.thematic_trimming_field_infos import (
    FIELDS_INFO,
    ThematicTrimmingFormFields860,
    ThematicTrimmingFormFields910,
    ThematicTrimmingFormFieldsBase,
)
from antarest.study.business.thematic_trimming_management import (
    ThematicTrimmingManager,
    get_fields_info,
)
from antarest.study.model import (
    STUDY_VERSION_7_0,
    STUDY_VERSION_8,
    STUDY_VERSION_8_2,
    STUDY_VERSION_8_3,
    STUDY_VERSION_8_4,
    STUDY_VERSION_8_6,
    STUDY_VERSION_9_1,
)
from antarest.study.storage.rawstudy.model.filesystem.config.model import FileStudyTreeConfig
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.rawstudy.model.filesystem.root.filestudytree import FileStudyTree
from antarest.study.storage.variantstudy.model.command.update_config import UpdateConfig
from antarest.study.storage.variantstudy.model.command_context import CommandContext


def test_thematic_trimming_config(command_context: CommandContext) -> None:
    thematic_trimming_manager = ThematicTrimmingManager(
        command_context=command_context,
    )

    config = FileStudyTreeConfig(
        study_path=Path("somepath"),
        path=Path("somepath"),
        study_id="",
        version=-1,
        areas={},
        sets={},
    )
    file_tree_mock = Mock(spec=FileStudyTree, context=Mock(), config=config)
    file_tree_mock.get.side_effect = [
        # For study version < 800:
        {},
        # For study version >= 800:
        {"variables selection": {"select_var -": ["AVL DTG"]}},
        # For study version >= 820:
        {"variables selection": {"select_var -": ["AVL DTG"]}},
        # For study version >= 830:
        {"variables selection": {"selected_vars_reset": True, "select_var -": ["DENS", "Profit by plant"]}},
        # For study version >= 840:
        {"variables selection": {"selected_vars_reset": False, "select_var +": ["CONG. FEE (ALG.)"]}},
        # For study version >= 860:
        {"variables selection": {"selected_vars_reset": True, "select_var -": ["STS inj by plant"]}},
        # For study version >= 910:
        {"variables selection": {"selected_vars_reset": True, "select_var -": ["STS by group"]}},
    ]

    study = Mock(StudyInterface)
    study.get_files.return_value = FileStudy(config=config, tree=file_tree_mock)

    study.version = config.version = STUDY_VERSION_7_0
    actual = thematic_trimming_manager.get_field_values(study)
    fields_info = get_fields_info(study.version)
    expected = ThematicTrimmingFormFieldsBase.model_validate(dict.fromkeys(fields_info, True))
    assert actual == expected

    study.version = config.version = STUDY_VERSION_8
    actual = thematic_trimming_manager.get_field_values(study)
    fields_info = get_fields_info(study.version)
    expected = ThematicTrimmingFormFieldsBase.model_validate(dict.fromkeys(fields_info, True))
    expected.avl_dtg = False
    assert actual == expected

    study.version = config.version = STUDY_VERSION_8_2
    actual = thematic_trimming_manager.get_field_values(study)
    fields_info = get_fields_info(study.version)
    expected = ThematicTrimmingFormFieldsBase.model_validate(dict.fromkeys(fields_info, True))
    expected.avl_dtg = False
    assert actual == expected

    study.version = config.version = STUDY_VERSION_8_3
    actual = thematic_trimming_manager.get_field_values(study)
    fields_info = get_fields_info(study.version)
    expected = ThematicTrimmingFormFieldsBase.model_validate(dict.fromkeys(fields_info, True))
    expected.dens = False
    expected.profit_by_plant = False
    assert actual == expected

    study.version = config.version = STUDY_VERSION_8_4
    study_version = study.version
    actual = thematic_trimming_manager.get_field_values(study)
    fields_info = get_fields_info(study_version)
    expected = ThematicTrimmingFormFieldsBase.model_validate(dict.fromkeys(fields_info, False))
    expected.cong_fee_alg = True
    assert actual == expected

    new_config = ThematicTrimmingFormFieldsBase.model_validate(dict.fromkeys(fields_info, True))
    new_config.coal = False
    thematic_trimming_manager.set_field_values(study, new_config)
    assert study.add_commands.called_with(
        UpdateConfig(
            target="settings/generaldata/variables selection",
            data={"select_var -": [FIELDS_INFO["coal"]["path"]]},
            command_context=command_context,
            study_version=study_version,
        )
    )

    new_config = ThematicTrimmingFormFieldsBase.model_validate(dict.fromkeys(fields_info, False))
    new_config.renw_1 = True
    thematic_trimming_manager.set_field_values(study, new_config)
    assert study.add_commands.called_with(
        UpdateConfig(
            target="settings/generaldata/variables selection",
            data={
                "selected_vars_reset": False,
                "select_var +": [FIELDS_INFO["renw_1"]["path"]],
            },
            command_context=command_context,
            study_version=study_version,
        )
    )

    assert len(FIELDS_INFO) == 95

    study.version = config.version = STUDY_VERSION_8_6
    actual = thematic_trimming_manager.get_field_values(study)
    fields_info = get_fields_info(study.version)
    expected = ThematicTrimmingFormFields860.model_validate(dict.fromkeys(fields_info, True))
    expected.sts_inj_by_plant = False
    assert actual == expected

    study.version = config.version = STUDY_VERSION_9_1
    actual = thematic_trimming_manager.get_field_values(study)
    fields_info = get_fields_info(study.version)
    expected = ThematicTrimmingFormFields910.model_validate(dict.fromkeys(fields_info, True))
    expected.sts_by_group = False
    assert actual == expected
