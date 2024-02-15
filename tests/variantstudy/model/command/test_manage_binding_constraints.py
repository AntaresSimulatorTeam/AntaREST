from unittest.mock import Mock

import numpy as np
import pytest

from antarest.study.storage.rawstudy.ini_reader import IniReader
from antarest.study.storage.rawstudy.model.filesystem.config.binding_constraint import (
    BindingConstraintFrequency,
    BindingConstraintOperator,
)
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
from antarest.study.storage.variantstudy.model.command.update_binding_constraint import UpdateBindingConstraint
from antarest.study.storage.variantstudy.model.command_context import CommandContext


# noinspection SpellCheckingInspection
@pytest.mark.parametrize("empty_study", ["empty_study_720.zip", "empty_study_870.zip"], indirect=True)
def test_manage_binding_constraint(empty_study: FileStudy, command_context: CommandContext):
    study_path = empty_study.config.study_path

    area1 = "area1"
    area2 = "area2"
    cluster = "cluster"
    CreateArea.parse_obj({"area_name": area1, "command_context": command_context}).apply(empty_study)
    CreateArea.parse_obj({"area_name": area2, "command_context": command_context}).apply(empty_study)
    CreateLink.parse_obj({"area1": area1, "area2": area2, "command_context": command_context}).apply(empty_study)
    CreateCluster.parse_obj(
        {"area_id": area1, "cluster_name": cluster, "parameters": {}, "command_context": command_context}
    ).apply(empty_study)

    bind1_cmd = CreateBindingConstraint(
        name="BD 1",
        time_step=BindingConstraintFrequency.HOURLY,
        operator=BindingConstraintOperator.LESS,
        coeffs={"area1%area2": [800, 30]},
        comments="Hello",
        command_context=command_context,
    )
    res = bind1_cmd.apply(empty_study)
    assert res.status

    bind2_cmd = CreateBindingConstraint(
        name="BD 2",
        enabled=False,
        time_step=BindingConstraintFrequency.DAILY,
        operator=BindingConstraintOperator.BOTH,
        coeffs={"area1.cluster": [50]},
        command_context=command_context,
    )
    res2 = bind2_cmd.apply(empty_study)
    assert res2.status

    if empty_study.config.version < 870:
        matrix_links = ["bd 1.txt.link", "bd 2.txt.link"]
    else:
        matrix_links = [
            # fmt: off
            "bd 1_lt.txt.link", "bd 1_eq.txt.link", "bd 1_gt.txt.link",
            "bd 2_lt.txt.link", "bd 2_eq.txt.link", "bd 2_gt.txt.link",
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
    if empty_study.config.version >= 830:
        expected_bd_1["filter-year-by-year"] = ""
        expected_bd_1["filter-synthesis"] = ""
        expected_bd_2["filter-year-by-year"] = ""
        expected_bd_2["filter-synthesis"] = ""
    if empty_study.config.version >= 870:
        expected_bd_1["group"] = "default"
        expected_bd_2["group"] = "default"

    assert bd_config.get("0") == expected_bd_1
    assert bd_config.get("1") == expected_bd_2

    if empty_study.config.version < 870:
        weekly_values = default_bc_weekly_daily.tolist()
        values = weekly_values
        less_term_matrix = None
        greater_term_matrix = None
    else:
        weekly_values = default_bc_weekly_daily_870.tolist()
        values = None
        less_term_matrix = weekly_values
        greater_term_matrix = weekly_values

    bind_update = UpdateBindingConstraint(
        id="bd 1",
        enabled=False,
        time_step=BindingConstraintFrequency.WEEKLY,
        operator=BindingConstraintOperator.BOTH,
        coeffs={"area1%area2": [800, 30]},
        values=values,
        less_term_matrix=less_term_matrix,
        greater_term_matrix=greater_term_matrix,
        command_context=command_context,
    )
    res = bind_update.apply(empty_study)
    assert res.status
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
    if empty_study.config.version >= 830:
        expected_bd_1["filter-year-by-year"] = ""
        expected_bd_1["filter-synthesis"] = ""
    if empty_study.config.version >= 870:
        expected_bd_1["group"] = "default"
    assert bd_config.get("0") == expected_bd_1

    remove_bind = RemoveBindingConstraint(id="bd 1", command_context=command_context)
    res3 = remove_bind.apply(empty_study)
    assert res3.status

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
    if empty_study.config.version >= 830:
        expected_bd_2["filter-year-by-year"] = ""
        expected_bd_2["filter-synthesis"] = ""
    if empty_study.config.version >= 870:
        expected_bd_2["group"] = "default"
    assert bd_config.get("0") == expected_bd_2


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
    )
    other_match = CreateBindingConstraint(
        name="foo",
        enabled=False,
        time_step=BindingConstraintFrequency.DAILY,
        operator=BindingConstraintOperator.BOTH,
        coeffs={"a": [0.3]},
        values=values,
        command_context=command_context,
    )
    other_not_match = CreateBindingConstraint(
        name="bar",
        enabled=False,
        time_step=BindingConstraintFrequency.DAILY,
        operator=BindingConstraintOperator.BOTH,
        coeffs={"a": [0.3]},
        command_context=command_context,
    )
    other_other = RemoveArea(id="id", command_context=command_context)
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
    )
    other_match = UpdateBindingConstraint(
        id="foo",
        enabled=False,
        time_step=BindingConstraintFrequency.DAILY,
        operator=BindingConstraintOperator.BOTH,
        coeffs={"a": [0.3]},
        values=values,
        command_context=command_context,
    )
    other_not_match = UpdateBindingConstraint(
        id="bar",
        enabled=False,
        time_step=BindingConstraintFrequency.DAILY,
        operator=BindingConstraintOperator.BOTH,
        coeffs={"a": [0.3]},
        command_context=command_context,
    )
    other_other = RemoveArea(id="id", command_context=command_context)
    assert base.match(other_match)
    assert not base.match(other_not_match)
    assert not base.match(other_other)
    assert base.match_signature() == "update_binding_constraint%foo"
    # check the matrices links
    matrix_id = command_context.matrix_service.create(values)
    assert base.get_inner_matrices() == [matrix_id]

    base = RemoveBindingConstraint(id="foo", command_context=command_context)
    other_match = RemoveBindingConstraint(id="foo", command_context=command_context)
    other_not_match = RemoveBindingConstraint(id="bar", command_context=command_context)
    other_other = RemoveLink(area1="id", area2="id2", command_context=command_context)
    assert base.match(other_match)
    assert not base.match(other_not_match)
    assert not base.match(other_other)
    assert base.match_signature() == "remove_binding_constraint%foo"
    assert base.get_inner_matrices() == []


def test_revert(command_context: CommandContext):
    hourly_values = default_bc_hourly.tolist()
    daily_values = default_bc_weekly_daily.tolist()
    weekly_values = default_bc_weekly_daily.tolist()
    base = CreateBindingConstraint(
        name="foo",
        enabled=False,
        time_step=BindingConstraintFrequency.DAILY,
        operator=BindingConstraintOperator.BOTH,
        coeffs={"a": [0.3]},
        values=daily_values,
        command_context=command_context,
    )
    assert CommandReverter().revert(base, [], Mock(spec=FileStudy)) == [
        RemoveBindingConstraint(id="foo", command_context=command_context)
    ]

    base = UpdateBindingConstraint(
        id="foo",
        enabled=False,
        time_step=BindingConstraintFrequency.DAILY,
        operator=BindingConstraintOperator.BOTH,
        coeffs={"a": [0.3]},
        values=daily_values,
        command_context=command_context,
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
            ),
            UpdateBindingConstraint(
                id="foo",
                enabled=True,
                time_step=BindingConstraintFrequency.HOURLY,
                operator=BindingConstraintOperator.BOTH,
                coeffs={"a": [0.3]},
                values=hourly_values,
                command_context=command_context,
            ),
        ],
        Mock(spec=FileStudy),
    ) == [
        UpdateBindingConstraint(
            id="foo",
            enabled=True,
            time_step=BindingConstraintFrequency.HOURLY,
            operator=BindingConstraintOperator.BOTH,
            coeffs={"a": [0.3]},
            values=hourly_values,
            command_context=command_context,
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
            ),
            CreateBindingConstraint(
                name="foo",
                enabled=True,
                time_step=BindingConstraintFrequency.HOURLY,
                operator=BindingConstraintOperator.EQUAL,
                coeffs={"a": [0.3]},
                values=hourly_values,
                command_context=command_context,
            ),
        ],
        Mock(spec=FileStudy),
    ) == [
        UpdateBindingConstraint(
            id="foo",
            enabled=True,
            time_step=BindingConstraintFrequency.HOURLY,
            operator=BindingConstraintOperator.EQUAL,
            coeffs={"a": [0.3]},
            values=hourly_matrix_id,
            command_context=command_context,
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
    )
    other_match = UpdateBindingConstraint(
        id="foo",
        enabled=False,
        time_step=BindingConstraintFrequency.DAILY,
        operator=BindingConstraintOperator.BOTH,
        coeffs={"a": [0.3]},
        values=values,
        command_context=command_context,
    )
    assert base.create_diff(other_match) == [other_match]

    base = RemoveBindingConstraint(id="foo", command_context=command_context)
    other_match = RemoveBindingConstraint(id="foo", command_context=command_context)
    assert base.create_diff(other_match) == []
