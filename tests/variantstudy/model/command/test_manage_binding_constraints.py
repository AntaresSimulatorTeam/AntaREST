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

from unittest.mock import Mock

import numpy as np
import pytest

from antarest.study.model import STUDY_VERSION_8_8
from antarest.study.storage.rawstudy.ini_reader import IniReader
from antarest.study.storage.rawstudy.model.filesystem.config.binding_constraint import (
    BindingConstraintFrequency,
    BindingConstraintOperator,
)
from antarest.study.storage.rawstudy.model.filesystem.config.field_validators import transform_name_to_id
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.business.command_extractor import CommandExtractor
from antarest.study.storage.variantstudy.business.command_reverter import CommandReverter
from antarest.study.storage.variantstudy.business.matrix_constants.binding_constraint.series_after_v87 import (
    default_bc_weekly_daily as default_bc_weekly_daily_870,
)
from antarest.study.storage.variantstudy.business.matrix_constants.binding_constraint.series_before_v87 import (
    default_bc_hourly,
    default_bc_weekly_daily,
)
from antarest.study.storage.variantstudy.model.command.create_area import CreateArea
from antarest.study.storage.variantstudy.model.command.create_binding_constraint import CreateBindingConstraint
from antarest.study.storage.variantstudy.model.command.create_cluster import CreateCluster
from antarest.study.storage.variantstudy.model.command.create_link import CreateLink
from antarest.study.storage.variantstudy.model.command.remove_area import RemoveArea
from antarest.study.storage.variantstudy.model.command.remove_binding_constraint import RemoveBindingConstraint
from antarest.study.storage.variantstudy.model.command.remove_link import RemoveLink
from antarest.study.storage.variantstudy.model.command.update_binding_constraint import (
    UpdateBindingConstraint,
    update_matrices_names,
)
from antarest.study.storage.variantstudy.model.command.update_scenario_builder import UpdateScenarioBuilder
from antarest.study.storage.variantstudy.model.command_context import CommandContext


# noinspection SpellCheckingInspection
@pytest.mark.parametrize("empty_study", ["empty_study_720.zip", "empty_study_870.zip"], indirect=True)
def test_manage_binding_constraint(empty_study: FileStudy, command_context: CommandContext):
    study_path = empty_study.config.study_path
    study_version = empty_study.config.version

    area1 = "area1"
    area2 = "area2"
    cluster = "cluster"
    CreateArea(area_name=area1, command_context=command_context, study_version=study_version).apply(empty_study)
    CreateArea(area_name=area2, command_context=command_context, study_version=study_version).apply(empty_study)
    CreateLink(area1=area1, area2=area2, command_context=command_context, study_version=study_version).apply(
        empty_study
    )
    CreateCluster(
        area_id=area1, cluster_name=cluster, parameters={}, command_context=command_context, study_version=study_version
    ).apply(empty_study)

    output = CreateBindingConstraint(
        name="BD 1",
        time_step=BindingConstraintFrequency.HOURLY,
        operator=BindingConstraintOperator.LESS,
        coeffs={"area1%area2": [800, 30]},
        comments="Hello",
        command_context=command_context,
        study_version=study_version,
    ).apply(empty_study)
    assert output.status, output.message

    output = CreateBindingConstraint(
        name="BD 2",
        enabled=False,
        time_step=BindingConstraintFrequency.DAILY,
        operator=BindingConstraintOperator.BOTH,
        coeffs={"area1.cluster": [50]},
        command_context=command_context,
        study_version=study_version,
    ).apply(empty_study)
    assert output.status, output.message

    if empty_study.config.version < 870:
        matrix_links = ["bd 1.txt.link", "bd 2.txt.link"]
    else:
        matrix_links = [
            # fmt: off
            "bd 1_lt.txt.link",
            "bd 2_lt.txt.link",
            "bd 2_gt.txt.link",
            # fmt: on
        ]
    for matrix_link in matrix_links:
        link_path = study_path / f"input/bindingconstraints/{matrix_link}"
        assert link_path.exists(), f"Missing matrix link: {matrix_link!r}"

    cfg_path = study_path / "input/bindingconstraints/bindingconstraints.ini"
    bd_config = IniReader().read(cfg_path)

    expected_bd_1 = {
        "name": "BD 1",
        "id": "bd 1",
        "enabled": True,
        "comments": "Hello",
        "area1%area2": "800.0%30",
        "operator": "less",
        "type": "hourly",
    }
    expected_bd_2 = {
        "name": "BD 2",
        "id": "bd 2",
        "enabled": False,
        "comments": "",
        "area1.cluster": 50.0,
        "operator": "both",
        "type": "daily",
    }
    if study_version >= 830:
        expected_bd_1["filter-year-by-year"] = ""
        expected_bd_1["filter-synthesis"] = ""
        expected_bd_2["filter-year-by-year"] = ""
        expected_bd_2["filter-synthesis"] = ""
    if study_version >= 870:
        expected_bd_1["group"] = "default"
        expected_bd_2["group"] = "default"

    assert bd_config.get("0") == expected_bd_1
    assert bd_config.get("1") == expected_bd_2

    if study_version < 870:
        weekly_values = default_bc_weekly_daily.tolist()
        values = weekly_values
        less_term_matrix = None
        greater_term_matrix = None
    else:
        weekly_values = default_bc_weekly_daily_870.tolist()
        values = None
        less_term_matrix = weekly_values
        greater_term_matrix = weekly_values

    output = UpdateBindingConstraint(
        id="bd 1",
        enabled=False,
        time_step=BindingConstraintFrequency.WEEKLY,
        operator=BindingConstraintOperator.BOTH,
        coeffs={"area1%area2": [800, 30]},
        values=values,
        less_term_matrix=less_term_matrix,
        greater_term_matrix=greater_term_matrix,
        command_context=command_context,
        study_version=study_version,
    ).apply(empty_study)
    assert output.status, output.message

    bd_config = IniReader().read(cfg_path)
    expected_bd_1 = {
        "name": "BD 1",
        "id": "bd 1",
        "enabled": False,
        "comments": "Hello",  # comments are not updated
        "area1%area2": "800.0%30",
        "operator": "both",
        "type": "weekly",
    }
    if study_version >= 830:
        expected_bd_1["filter-year-by-year"] = ""
        expected_bd_1["filter-synthesis"] = ""
    if study_version >= 870:
        expected_bd_1["group"] = "default"
    assert bd_config.get("0") == expected_bd_1

    if study_version >= 870:
        # Add scenario builder data
        output = UpdateScenarioBuilder(
            data={"Default Ruleset": {"bc,default,0": 1}}, command_context=command_context, study_version=study_version
        ).apply(study_data=empty_study)
        assert output.status, output.message

    output = RemoveBindingConstraint(id="bd 1", command_context=command_context, study_version=study_version).apply(
        empty_study
    )
    assert output.status, output.message

    if study_version >= 870:
        # Check that the scenario builder is not yet updated, because "BD 2" is still present
        rulesets = empty_study.tree.get(["settings", "scenariobuilder"])
        assert rulesets == {"Default Ruleset": {"bc,default,0": 1}}

    for matrix_link in matrix_links:
        link_path = study_path / f"input/bindingconstraints/{matrix_link}"
        if matrix_link.startswith("bd 1"):
            assert not link_path.exists(), f"Matrix link not removed: {matrix_link!r}"
        elif matrix_link.startswith("bd 2"):
            assert link_path.exists(), f"Matrix link removed: {matrix_link!r}"
        else:
            raise NotImplementedError(f"Unexpected matrix link: {matrix_link!r}")

    bd_config = IniReader().read(cfg_path)
    assert len(bd_config) == 1
    expected_bd_2 = {
        "name": "BD 2",
        "id": "bd 2",
        "enabled": False,
        "area1.cluster": 50.0,
        "comments": "",
        "operator": "both",
        "type": "daily",
    }
    if study_version >= 830:
        expected_bd_2["filter-year-by-year"] = ""
        expected_bd_2["filter-synthesis"] = ""
    if study_version >= 870:
        expected_bd_2["group"] = "default"
    assert bd_config.get("0") == expected_bd_2

    output = RemoveBindingConstraint(id="bd 2", command_context=command_context, study_version=study_version).apply(
        empty_study
    )
    assert output.status, output.message

    if study_version >= 870:
        # Check that the scenario builder is updated
        rulesets = empty_study.tree.get(["settings", "scenariobuilder"])
        assert rulesets == {"Default Ruleset": {}}


@pytest.mark.parametrize("empty_study", ["empty_study_870.zip"], indirect=True)
def test_scenario_builder(empty_study: FileStudy, command_context: CommandContext):
    """
    Test that the scenario builder is updated when a binding constraint group is renamed or removed
    """
    # This test requires a study with version >= 870, which support "scenarised" binding constraints.
    study_version = empty_study.config.version
    assert study_version >= 870

    # Create two areas and a link between them:
    areas = {name: transform_name_to_id(name) for name in ["Area X", "Area Y"]}
    for area in areas.values():
        output = CreateArea(area_name=area, command_context=command_context, study_version=study_version).apply(
            empty_study
        )
        assert output.status, output.message
    output = CreateLink(
        area1=areas["Area X"], area2=areas["Area Y"], command_context=command_context, study_version=study_version
    ).apply(empty_study)
    assert output.status, output.message
    link_id = f"{areas['Area X']}%{areas['Area Y']}"

    # Create a binding constraint in a specific group:
    bc_group = "Group 1"
    output = CreateBindingConstraint(
        name="BD 1",
        enabled=False,
        time_step=BindingConstraintFrequency.DAILY,
        operator=BindingConstraintOperator.BOTH,
        coeffs={link_id: [0.3]},
        group=bc_group,
        command_context=command_context,
        study_version=study_version,
    ).apply(empty_study)
    assert output.status, output.message

    # Create a rule in the scenario builder for the binding constraint group:
    output = UpdateScenarioBuilder(
        data={"Default Ruleset": {f"bc,{bc_group.lower()},0": 1}},  # group name in lowercase
        command_context=command_context,
        study_version=study_version,
    ).apply(study_data=empty_study)
    assert output.status, output.message

    # Here, we have a binding constraint between "Area X" and "Area Y" in the group "Group 1"
    # and a rule in the scenario builder for this group.
    # If we update the group name in the BC, the scenario builder should be updated
    output = UpdateBindingConstraint(
        id="bd 1", group="Group 2", command_context=command_context, study_version=study_version
    ).apply(empty_study)
    assert output.status, output.message

    # Check the BC rule is removed from the scenario builder
    rulesets = empty_study.tree.get(["settings", "scenariobuilder"])
    assert rulesets == {"Default Ruleset": {}}


def test_match(command_context: CommandContext):
    values = default_bc_weekly_daily.tolist()
    base = CreateBindingConstraint(
        name="foo",
        enabled=False,
        time_step=BindingConstraintFrequency.DAILY,
        operator=BindingConstraintOperator.BOTH,
        coeffs={"a": [0.3]},
        values=values,
        command_context=command_context,
        study_version=STUDY_VERSION_8_8,
    )
    other_match = CreateBindingConstraint(
        name="foo",
        enabled=False,
        time_step=BindingConstraintFrequency.DAILY,
        operator=BindingConstraintOperator.BOTH,
        coeffs={"a": [0.3]},
        values=values,
        command_context=command_context,
        study_version=STUDY_VERSION_8_8,
    )
    other_not_match = CreateBindingConstraint(
        name="bar",
        enabled=False,
        time_step=BindingConstraintFrequency.DAILY,
        operator=BindingConstraintOperator.BOTH,
        coeffs={"a": [0.3]},
        command_context=command_context,
        study_version=STUDY_VERSION_8_8,
    )
    other_other = RemoveArea(id="id", command_context=command_context, study_version=STUDY_VERSION_8_8)
    assert base.match(other_match)
    assert not base.match(other_not_match)
    assert not base.match(other_other)
    assert base.match_signature() == "create_binding_constraint%foo"
    # check the matrices links
    matrix_id = command_context.matrix_service.create(values)
    assert base.get_inner_matrices() == [matrix_id]

    base = UpdateBindingConstraint(
        id="foo",
        enabled=False,
        time_step=BindingConstraintFrequency.DAILY,
        operator=BindingConstraintOperator.BOTH,
        coeffs={"a": [0.3]},
        values=values,
        command_context=command_context,
        study_version=STUDY_VERSION_8_8,
    )
    other_match = UpdateBindingConstraint(
        id="foo",
        enabled=False,
        time_step=BindingConstraintFrequency.DAILY,
        operator=BindingConstraintOperator.BOTH,
        coeffs={"a": [0.3]},
        values=values,
        command_context=command_context,
        study_version=STUDY_VERSION_8_8,
    )
    other_not_match = UpdateBindingConstraint(
        id="bar",
        enabled=False,
        time_step=BindingConstraintFrequency.DAILY,
        operator=BindingConstraintOperator.BOTH,
        coeffs={"a": [0.3]},
        command_context=command_context,
        study_version=STUDY_VERSION_8_8,
    )
    other_other = RemoveArea(id="id", command_context=command_context, study_version=STUDY_VERSION_8_8)
    assert base.match(other_match)
    assert not base.match(other_not_match)
    assert not base.match(other_other)
    assert base.match_signature() == "update_binding_constraint%foo"
    # check the matrices links
    matrix_id = command_context.matrix_service.create(values)
    assert base.get_inner_matrices() == [matrix_id]

    base = RemoveBindingConstraint(id="foo", command_context=command_context, study_version=STUDY_VERSION_8_8)
    other_match = RemoveBindingConstraint(id="foo", command_context=command_context, study_version=STUDY_VERSION_8_8)
    other_not_match = RemoveBindingConstraint(
        id="bar", command_context=command_context, study_version=STUDY_VERSION_8_8
    )
    other_other = RemoveLink(area1="id", area2="id2", command_context=command_context, study_version=STUDY_VERSION_8_8)
    assert base.match(other_match)
    assert not base.match(other_not_match)
    assert not base.match(other_other)
    assert base.match_signature() == "remove_binding_constraint%foo"
    assert base.get_inner_matrices() == []


def test_revert(command_context: CommandContext):
    hourly_values = default_bc_hourly.tolist()
    daily_values = default_bc_weekly_daily.tolist()
    weekly_values = default_bc_weekly_daily.tolist()
    file_study = Mock(spec=FileStudy)
    file_study.config.version = STUDY_VERSION_8_8
    base = CreateBindingConstraint(
        name="foo",
        enabled=False,
        time_step=BindingConstraintFrequency.DAILY,
        operator=BindingConstraintOperator.BOTH,
        coeffs={"a": [0.3]},
        values=daily_values,
        command_context=command_context,
        study_version=STUDY_VERSION_8_8,
    )
    assert CommandReverter().revert(base, [], file_study) == [
        RemoveBindingConstraint(id="foo", command_context=command_context, study_version=STUDY_VERSION_8_8)
    ]

    base = UpdateBindingConstraint(
        id="foo",
        enabled=False,
        time_step=BindingConstraintFrequency.DAILY,
        operator=BindingConstraintOperator.BOTH,
        coeffs={"a": [0.3]},
        values=daily_values,
        command_context=command_context,
        study_version=STUDY_VERSION_8_8,
    )
    mock_command_extractor = Mock(spec=CommandExtractor)
    object.__setattr__(
        base,
        "get_command_extractor",
        Mock(return_value=mock_command_extractor),
    )
    assert CommandReverter().revert(
        base,
        [
            UpdateBindingConstraint(
                id="foo",
                enabled=True,
                time_step=BindingConstraintFrequency.WEEKLY,
                operator=BindingConstraintOperator.BOTH,
                coeffs={"a": [0.3]},
                values=weekly_values,
                command_context=command_context,
                study_version=STUDY_VERSION_8_8,
            ),
            UpdateBindingConstraint(
                id="foo",
                enabled=True,
                time_step=BindingConstraintFrequency.HOURLY,
                operator=BindingConstraintOperator.BOTH,
                coeffs={"a": [0.3]},
                values=hourly_values,
                command_context=command_context,
                study_version=STUDY_VERSION_8_8,
            ),
        ],
        file_study,
    ) == [
        UpdateBindingConstraint(
            id="foo",
            enabled=True,
            time_step=BindingConstraintFrequency.HOURLY,
            operator=BindingConstraintOperator.BOTH,
            coeffs={"a": [0.3]},
            values=hourly_values,
            command_context=command_context,
            study_version=STUDY_VERSION_8_8,
        )
    ]
    # check the matrices links
    hourly_matrix_id = command_context.matrix_service.create(hourly_values)
    assert CommandReverter().revert(
        base,
        [
            UpdateBindingConstraint(
                id="foo",
                enabled=True,
                time_step=BindingConstraintFrequency.WEEKLY,
                operator=BindingConstraintOperator.BOTH,
                coeffs={"a": [0.3]},
                values=weekly_values,
                command_context=command_context,
                study_version=STUDY_VERSION_8_8,
            ),
            CreateBindingConstraint(
                name="foo",
                enabled=True,
                time_step=BindingConstraintFrequency.HOURLY,
                operator=BindingConstraintOperator.EQUAL,
                coeffs={"a": [0.3]},
                values=hourly_values,
                command_context=command_context,
                study_version=STUDY_VERSION_8_8,
            ),
        ],
        file_study,
    ) == [
        UpdateBindingConstraint(
            id="foo",
            enabled=True,
            time_step=BindingConstraintFrequency.HOURLY,
            operator=BindingConstraintOperator.EQUAL,
            filter_year_by_year="",
            filter_synthesis="",
            coeffs={"a": [0.3]},
            values=hourly_matrix_id,
            command_context=command_context,
            study_version=STUDY_VERSION_8_8,
        )
    ]
    study = FileStudy(config=Mock(), tree=Mock())
    CommandReverter().revert(base, [], study)
    mock_command_extractor.extract_binding_constraint.assert_called_with(study, "foo")


def test_create_diff(command_context: CommandContext):
    values_a = np.random.rand(366, 3).tolist()
    base = CreateBindingConstraint(
        name="foo",
        enabled=False,
        time_step=BindingConstraintFrequency.DAILY,
        operator=BindingConstraintOperator.BOTH,
        coeffs={"a": [0.3]},
        values=values_a,
        command_context=command_context,
        study_version=STUDY_VERSION_8_8,
    )

    values_b = np.random.rand(8784, 3).tolist()
    matrix_b_id = command_context.matrix_service.create(values_b)
    other_match = CreateBindingConstraint(
        name="foo",
        enabled=True,
        time_step=BindingConstraintFrequency.HOURLY,
        operator=BindingConstraintOperator.EQUAL,
        coeffs={"b": [0.3]},
        values=matrix_b_id,
        command_context=command_context,
        study_version=STUDY_VERSION_8_8,
    )
    assert base.create_diff(other_match) == [
        UpdateBindingConstraint(
            id="foo",
            enabled=True,
            time_step=BindingConstraintFrequency.HOURLY,
            operator=BindingConstraintOperator.EQUAL,
            coeffs={"b": [0.3]},
            values=matrix_b_id,
            command_context=command_context,
            study_version=STUDY_VERSION_8_8,
        )
    ]

    values = default_bc_weekly_daily.tolist()
    base = UpdateBindingConstraint(
        id="foo",
        enabled=False,
        time_step=BindingConstraintFrequency.DAILY,
        operator=BindingConstraintOperator.BOTH,
        coeffs={"a": [0.3]},
        values=values,
        command_context=command_context,
        study_version=STUDY_VERSION_8_8,
    )
    other_match = UpdateBindingConstraint(
        id="foo",
        enabled=False,
        time_step=BindingConstraintFrequency.DAILY,
        operator=BindingConstraintOperator.BOTH,
        coeffs={"a": [0.3]},
        values=values,
        command_context=command_context,
        study_version=STUDY_VERSION_8_8,
    )
    assert base.create_diff(other_match) == [other_match]

    base = RemoveBindingConstraint(id="foo", command_context=command_context, study_version=STUDY_VERSION_8_8)
    other_match = RemoveBindingConstraint(id="foo", command_context=command_context, study_version=STUDY_VERSION_8_8)
    assert base.create_diff(other_match) == []


@pytest.mark.parametrize(
    "existing_operator, new_operator",
    [
        (BindingConstraintOperator.LESS, BindingConstraintOperator.LESS),
        (BindingConstraintOperator.LESS, BindingConstraintOperator.GREATER),
        (BindingConstraintOperator.LESS, BindingConstraintOperator.BOTH),
        (BindingConstraintOperator.LESS, BindingConstraintOperator.EQUAL),
        (BindingConstraintOperator.GREATER, BindingConstraintOperator.LESS),
        (BindingConstraintOperator.GREATER, BindingConstraintOperator.GREATER),
        (BindingConstraintOperator.GREATER, BindingConstraintOperator.BOTH),
        (BindingConstraintOperator.GREATER, BindingConstraintOperator.EQUAL),
        (BindingConstraintOperator.BOTH, BindingConstraintOperator.LESS),
        (BindingConstraintOperator.BOTH, BindingConstraintOperator.GREATER),
        (BindingConstraintOperator.BOTH, BindingConstraintOperator.BOTH),
        (BindingConstraintOperator.BOTH, BindingConstraintOperator.EQUAL),
        (BindingConstraintOperator.EQUAL, BindingConstraintOperator.LESS),
        (BindingConstraintOperator.EQUAL, BindingConstraintOperator.GREATER),
        (BindingConstraintOperator.EQUAL, BindingConstraintOperator.BOTH),
        (BindingConstraintOperator.EQUAL, BindingConstraintOperator.EQUAL),
    ],
)
@pytest.mark.parametrize("empty_study", ["empty_study_870.zip"], indirect=True)
def test__update_matrices_names(
    empty_study: FileStudy,
    command_context: CommandContext,
    existing_operator: BindingConstraintOperator,
    new_operator: BindingConstraintOperator,
):
    study_path = empty_study.config.study_path
    study_version = empty_study.config.version

    all_file_templates = {"{bc_id}_eq.txt.link", "{bc_id}_gt.txt.link", "{bc_id}_lt.txt.link"}

    operator_matrix_file_map = {
        BindingConstraintOperator.EQUAL: ["{bc_id}_eq.txt.link"],
        BindingConstraintOperator.GREATER: ["{bc_id}_gt.txt.link"],
        BindingConstraintOperator.LESS: ["{bc_id}_lt.txt.link"],
        BindingConstraintOperator.BOTH: ["{bc_id}_lt.txt.link", "{bc_id}_gt.txt.link"],
    }

    area1 = "area1"
    area2 = "area2"
    cluster = "cluster"
    CreateArea(area_name=area1, command_context=command_context, study_version=study_version).apply(empty_study)
    CreateArea(area_name=area2, command_context=command_context, study_version=study_version).apply(empty_study)
    CreateLink(area1=area1, area2=area2, command_context=command_context, study_version=study_version).apply(
        empty_study
    )
    CreateCluster(
        area_id=area1, cluster_name=cluster, parameters={}, command_context=command_context, study_version=study_version
    ).apply(empty_study)

    # create a binding constraint
    _ = CreateBindingConstraint(
        name="BD_RENAME_MATRICES",
        time_step=BindingConstraintFrequency.HOURLY,
        operator=existing_operator,
        coeffs={"area1%area2": [800, 30]},
        command_context=command_context,
        study_version=study_version,
    ).apply(empty_study)

    # check that the matrices are created
    file_templates = set(operator_matrix_file_map[existing_operator])
    superfluous_templates = all_file_templates - file_templates
    existing_matrices = [file_template.format(bc_id="bd_rename_matrices") for file_template in file_templates]
    superfluous_matrices = [file_template.format(bc_id="bd_rename_matrices") for file_template in superfluous_templates]
    for matrix_link in existing_matrices:
        link_path = study_path / f"input/bindingconstraints/{matrix_link}"
        assert link_path.exists(), f"Missing matrix link: {matrix_link!r}"
    for matrix_link in superfluous_matrices:
        link_path = study_path / f"input/bindingconstraints/{matrix_link}"
        assert not link_path.exists(), f"Superfluous matrix link: {matrix_link!r}"

    # update matrices names
    update_matrices_names(
        file_study=empty_study,
        bc_id="bd_rename_matrices",
        existing_operator=existing_operator,
        new_operator=new_operator,
    )

    # check that the matrices are renamed
    file_templates = set(operator_matrix_file_map[new_operator])
    superfluous_templates = all_file_templates - file_templates
    new_matrices = [file_template.format(bc_id="bd_rename_matrices") for file_template in file_templates]
    superfluous_matrices = [file_template.format(bc_id="bd_rename_matrices") for file_template in superfluous_templates]
    for matrix_link in new_matrices:
        link_path = study_path / f"input/bindingconstraints/{matrix_link}"
        assert link_path.exists(), f"Missing matrix link: {matrix_link!r}"
    for matrix_link in superfluous_matrices:
        link_path = study_path / f"input/bindingconstraints/{matrix_link}"
        assert not link_path.exists(), f"Superfluous matrix link: {matrix_link!r}"
