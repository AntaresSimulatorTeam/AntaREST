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

import pytest

from antarest.core.serde.ini_reader import read_ini
from antarest.study.business.model.thermal_cluster_model import ThermalClusterCreation
from antarest.study.storage.rawstudy.model.filesystem.config.binding_constraint import (
    BindingConstraintFrequency,
    BindingConstraintOperator,
)
from antarest.study.storage.rawstudy.model.filesystem.config.identifier import transform_name_to_id
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.business.matrix_constants.binding_constraint.series_after_v87 import (
    default_bc_weekly_daily as default_bc_weekly_daily_870,
)
from antarest.study.storage.variantstudy.business.matrix_constants.binding_constraint.series_before_v87 import (
    default_bc_weekly_daily,
)
from antarest.study.storage.variantstudy.model.command.create_area import CreateArea
from antarest.study.storage.variantstudy.model.command.create_binding_constraint import CreateBindingConstraint
from antarest.study.storage.variantstudy.model.command.create_cluster import CreateCluster
from antarest.study.storage.variantstudy.model.command.create_link import CreateLink
from antarest.study.storage.variantstudy.model.command.remove_binding_constraint import RemoveBindingConstraint
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
        area_id=area1,
        parameters=ThermalClusterCreation(name=cluster),
        command_context=command_context,
        study_version=study_version,
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
    bd_config = read_ini(cfg_path)

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

    bd_config = read_ini(cfg_path)
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

    bd_config = read_ini(cfg_path)
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
        area_id=area1,
        parameters=ThermalClusterCreation(name=cluster),
        command_context=command_context,
        study_version=study_version,
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
