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

from antares.study.version import StudyVersion

from antarest.study.business.study_interface import StudyInterface
from antarest.study.business.thematic_trimming_field_infos import FIELDS_INFO
from antarest.study.business.thematic_trimming_management import (
    ThematicTrimmingFormFields,
    ThematicTrimmingManager,
    get_fields_info,
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
    file_tree_mock = Mock(spec=FileStudyTree, matrix_mapper=Mock(), config=config)
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
    ]

    study = Mock(StudyInterface)
    study.get_files.return_value = FileStudy(config=config, tree=file_tree_mock)

    study.version = config.version = 700
    actual = thematic_trimming_manager.get_field_values(study)
    fields_info = get_fields_info(StudyVersion.parse(study.version))
    expected = ThematicTrimmingFormFields(**dict.fromkeys(fields_info, True))
    assert actual == expected

    study.version = config.version = 800
    actual = thematic_trimming_manager.get_field_values(study)
    fields_info = get_fields_info(StudyVersion.parse(study.version))
    expected = ThematicTrimmingFormFields(**dict.fromkeys(fields_info, True))
    expected.avl_dtg = False
    assert actual == expected

    study.version = config.version = 820
    actual = thematic_trimming_manager.get_field_values(study)
    fields_info = get_fields_info(StudyVersion.parse(study.version))
    expected = ThematicTrimmingFormFields(**dict.fromkeys(fields_info, True))
    expected.avl_dtg = False
    assert actual == expected

    study.version = config.version = 830
    actual = thematic_trimming_manager.get_field_values(study)
    fields_info = get_fields_info(StudyVersion.parse(study.version))
    expected = ThematicTrimmingFormFields(**dict.fromkeys(fields_info, True))
    expected.dens = False
    expected.profit_by_plant = False
    assert actual == expected

    study.version = config.version = 840
    study_version = StudyVersion.parse(study.version)
    actual = thematic_trimming_manager.get_field_values(study)
    fields_info = get_fields_info(study_version)
    expected = ThematicTrimmingFormFields(**dict.fromkeys(fields_info, False))
    expected.cong_fee_alg = True
    assert actual == expected

    new_config = ThematicTrimmingFormFields(**dict.fromkeys(fields_info, True))
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

    new_config = ThematicTrimmingFormFields(**dict.fromkeys(fields_info, False))
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

    assert len(FIELDS_INFO) == 94
