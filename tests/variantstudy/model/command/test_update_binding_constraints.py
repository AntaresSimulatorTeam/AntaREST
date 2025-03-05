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

from unittest.mock import Mock

import pytest
from antares.study.version import StudyVersion

from antarest.study.business.binding_constraint_management import ConstraintInput
from antarest.study.storage.rawstudy.model.filesystem.config.binding_constraint import (
    BindingConstraintFrequency,
    BindingConstraintOperator,
)
from antarest.study.storage.rawstudy.model.filesystem.config.model import BindingConstraintDTO, FileStudyTreeConfig
from antarest.study.storage.variantstudy.business.matrix_constants.binding_constraint.series_after_v87 import (
    default_bc_weekly_daily as default_bc_weekly_daily_87,
)
from antarest.study.storage.variantstudy.business.matrix_constants.binding_constraint.series_before_v87 import (
    default_bc_hourly as default_bc_hourly_86,
)
from antarest.study.storage.variantstudy.model.command.create_binding_constraint import BindingConstraintProperties
from antarest.study.storage.variantstudy.model.command.update_binding_constraints import (
    UpdateBindingConstraints,
    generate_replacement_matrices,
)
from antarest.study.storage.variantstudy.model.command_context import CommandContext


@pytest.fixture
def binding_constraint_properties():
    return {
        "bc_1": ConstraintInput(group="new_group1", operator="greater", time_step="daily"),
        "bc_2": ConstraintInput(group="new_group2", operator="less", time_step="hourly"),
    }


@pytest.fixture
def file_study():
    fs = Mock()
    fs.tree.get.return_value = {
        "1": {
            "id": "bc_1",
            "group": "old_group1",
            "areas": ["area1"],
            "clusters": ["cluster1"],
            "operator": "greater",
            "type": "hourly",
        },
        "2": {
            "id": "bc_2",
            "group": "old_group2",
            "areas": ["area2"],
            "clusters": ["cluster2"],
            "operator": "less",
            "type": "daily",
        },
    }
    return fs


@pytest.fixture
def file_study_tree_config():
    file_study_tree_config = Mock(spec=FileStudyTreeConfig)
    file_study_tree_config.bindings = [
        BindingConstraintDTO(
            id="bc_0",
            group="old_group1",
            areas=["area1"],
            clusters=["cluster1"],
            operator="greater",
            time_step="daily",
        ),
        BindingConstraintDTO(
            id="bc_1",
            group="old_group1",
            areas=["area1"],
            clusters=["cluster1"],
            operator="greater",
            time_step="daily",
        ),
        BindingConstraintDTO(
            id="bc_2",
            group="old_group2",
            areas=["area2"],
            clusters=["cluster2"],
            operator="less",
            time_step="hourly",
        ),
        BindingConstraintDTO(
            id="bc_3",
            group="old_group2",
            areas=["area2"],
            clusters=["cluster2"],
            operator="less",
            time_step="hourly",
        ),
    ]
    return file_study_tree_config


def test_apply_config(file_study_tree_config, binding_constraint_properties):
    command = UpdateBindingConstraints(
        study_version=StudyVersion(870),
        bc_props_by_id=binding_constraint_properties,
        command_context=Mock(spec=CommandContext),
    )
    output, _ = command._apply_config(file_study_tree_config)
    assert output.status is True
    # bc_0 is not in bc_props_by_id, so it should not be updated
    assert file_study_tree_config.bindings[0].group == "old_group1"
    # bc_1 is in bc_props_by_id, so it should be updated
    assert file_study_tree_config.bindings[1].group == "new_group1"
    assert file_study_tree_config.bindings[1].operator == "greater"
    assert file_study_tree_config.bindings[1].time_step == "daily"
    # bc_2 is in bc_props_by_id, so it should be updated
    assert file_study_tree_config.bindings[2].group == "new_group2"
    assert file_study_tree_config.bindings[2].operator == "less"
    assert file_study_tree_config.bindings[2].time_step == "hourly"
    # bc_3 is not in bc_props_by_id, so it should not be updated
    assert file_study_tree_config.bindings[3].group == "old_group2"


def test_check_version_consistency(binding_constraint_properties):
    values = {
        "bc_props_by_id": binding_constraint_properties,
        "study_version": StudyVersion(870),
    }
    validated_values = UpdateBindingConstraints.check_version_consistency(values)
    assert validated_values["bc_props_by_id"]["bc_1"].group == "new_group1"
    assert validated_values["bc_props_by_id"]["bc_2"].group == "new_group2"


def test_apply(binding_constraint_properties, file_study):
    command = UpdateBindingConstraints(
        study_version=StudyVersion(870),
        bc_props_by_id=binding_constraint_properties,
        command_context=Mock(spec=CommandContext),
    )
    output = command._apply(file_study)
    assert output.status is True
    file_study.tree.save.assert_called_with(
        {
            "1": {
                "id": "bc_1",
                "group": "new_group1",
                "areas": ["area1"],
                "clusters": ["cluster1"],
                "operator": "greater",
                "time_step": "daily",
                "type": "daily",
            },
            "2": {
                "id": "bc_2",
                "group": "new_group2",
                "areas": ["area2"],
                "clusters": ["cluster2"],
                "operator": "less",
                "time_step": "hourly",
                "type": "hourly",
            },
        },
        ["input", "bindingconstraints", "bindingconstraints"],
    )


def test_to_dto(binding_constraint_properties):
    command = UpdateBindingConstraints(
        study_version=StudyVersion(870),
        bc_props_by_id=binding_constraint_properties,
        command_context=Mock(spec=CommandContext),
    )
    dto = command.to_dto()
    assert dto.action == "update_binding_constraints"
    assert dto.version == 1
    assert dto.study_version == StudyVersion(870)


def test_generate_replacement_matrices_before_v87():
    bc_id = "bc_1"

    # 8,6,0 HOURLY GREATER
    study_version = StudyVersion(8, 6)
    bc_props = Mock(spec=BindingConstraintProperties)
    bc_props.time_step = BindingConstraintFrequency.HOURLY.value
    operator = BindingConstraintOperator.GREATER

    matrices = list(generate_replacement_matrices(bc_id, study_version, bc_props, operator))
    assert len(matrices) == 1
    assert matrices[0][0] == f"input/bindingconstraints/{bc_id}"
    assert matrices[0][1] == default_bc_hourly_86.tolist()

    # 8,7,0 DAILY BOTH
    bc_id = "bc_1"
    study_version = StudyVersion(8, 7)
    bc_props = Mock(spec=BindingConstraintProperties)
    bc_props.time_step = BindingConstraintFrequency.DAILY.value
    operator = BindingConstraintOperator.BOTH

    matrices = list(generate_replacement_matrices(bc_id, study_version, bc_props, operator))
    assert len(matrices) == 2
    assert matrices[0][0] == f"input/bindingconstraints/{bc_id}_lt"
    assert matrices[0][1] == default_bc_weekly_daily_87.tolist()
    assert matrices[1][0] == f"input/bindingconstraints/{bc_id}_gt"
    assert matrices[1][1] == default_bc_weekly_daily_87.tolist()

    # 8,7,0 WEEKLY LESS
    bc_id = "bc_1"
    study_version = StudyVersion(8, 7)
    bc_props = Mock(spec=BindingConstraintProperties)
    bc_props.time_step = BindingConstraintFrequency.WEEKLY.value
    operator = BindingConstraintOperator.LESS

    matrices = list(generate_replacement_matrices(bc_id, study_version, bc_props, operator))
    assert len(matrices) == 1
    target = f"input/bindingconstraints/{bc_id}_lt"
    assert matrices[0][0] == target
    assert matrices[0][1] == default_bc_weekly_daily_87.tolist()
