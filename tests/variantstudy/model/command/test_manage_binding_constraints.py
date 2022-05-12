from unittest.mock import Mock

from antarest.study.storage.rawstudy.io.reader import IniReader
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.rawstudy.model.filesystem.folder_node import (
    ChildNotFoundError,
)
from antarest.study.storage.variantstudy.business.command_extractor import (
    CommandExtractor,
)
from antarest.study.storage.variantstudy.business.command_reverter import (
    CommandReverter,
)
from antarest.study.storage.variantstudy.model.command.common import (
    BindingConstraintOperator,
    TimeStep,
)
from antarest.study.storage.variantstudy.model.command.create_area import (
    CreateArea,
)
from antarest.study.storage.variantstudy.model.command.create_binding_constraint import (
    CreateBindingConstraint,
)
from antarest.study.storage.variantstudy.model.command.create_cluster import (
    CreateCluster,
)
from antarest.study.storage.variantstudy.model.command.create_link import (
    CreateLink,
)
from antarest.study.storage.variantstudy.model.command.remove_area import (
    RemoveArea,
)
from antarest.study.storage.variantstudy.model.command.remove_binding_constraint import (
    RemoveBindingConstraint,
)
from antarest.study.storage.variantstudy.model.command.remove_link import (
    RemoveLink,
)
from antarest.study.storage.variantstudy.model.command.update_binding_constraint import (
    UpdateBindingConstraint,
)
from antarest.study.storage.variantstudy.model.command_context import (
    CommandContext,
)


def test_manage_binding_constraint(
    empty_study: FileStudy, command_context: CommandContext
):
    study_path = empty_study.config.study_path

    area1 = "area1"
    area2 = "area2"
    cluster = "cluster"
    CreateArea.parse_obj(
        {
            "area_name": area1,
            "command_context": command_context,
        }
    ).apply(empty_study)
    CreateArea.parse_obj(
        {
            "area_name": area2,
            "command_context": command_context,
        }
    ).apply(empty_study)
    CreateLink.parse_obj(
        {
            "area1": area1,
            "area2": area2,
            "command_context": command_context,
        }
    ).apply(empty_study)
    CreateCluster.parse_obj(
        {
            "area_id": area1,
            "cluster_name": cluster,
            "parameters": {},
            "command_context": command_context,
        }
    ).apply(empty_study)

    bind1_cmd = CreateBindingConstraint(
        name="BD 1",
        time_step=TimeStep.HOURLY,
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
        time_step=TimeStep.DAILY,
        operator=BindingConstraintOperator.BOTH,
        coeffs={"area1.cluster": [50]},
        command_context=command_context,
    )
    res2 = bind2_cmd.apply(empty_study)
    assert res2.status

    assert (
        study_path / "input" / "bindingconstraints" / "bd 1.txt.link"
    ).exists()
    assert (
        study_path / "input" / "bindingconstraints" / "bd 2.txt.link"
    ).exists()
    bd_config = IniReader().read(
        study_path / "input" / "bindingconstraints" / "bindingconstraints.ini"
    )
    assert bd_config.get("0") == {
        "name": "BD 1",
        "id": "bd 1",
        "enabled": True,
        "comments": "Hello",
        "area1%area2": "800.0%30",
        "operator": "less",
        "type": "hourly",
    }
    assert bd_config.get("1") == {
        "name": "BD 2",
        "id": "bd 2",
        "enabled": False,
        "area1.cluster": 50.0,
        "operator": "both",
        "type": "daily",
    }

    bind_update = UpdateBindingConstraint(
        id="bd 1",
        enabled=False,
        time_step=TimeStep.WEEKLY,
        operator=BindingConstraintOperator.BOTH,
        coeffs={"area1%area2": [800, 30]},
        values=[[0]],
        command_context=command_context,
    )
    res = bind_update.apply(empty_study)
    assert res.status
    bd_config = IniReader().read(
        study_path / "input" / "bindingconstraints" / "bindingconstraints.ini"
    )
    assert bd_config.get("0") == {
        "name": "BD 1",
        "id": "bd 1",
        "enabled": False,
        "area1%area2": "800.0%30",
        "operator": "both",
        "type": "weekly",
    }

    remove_bind = RemoveBindingConstraint(
        id="bd 1", command_context=command_context
    )
    res3 = remove_bind.apply(empty_study)
    assert res3.status
    assert not (
        study_path / "input" / "bindingconstraints" / "bd 1.txt.link"
    ).exists()
    bd_config = IniReader().read(
        study_path / "input" / "bindingconstraints" / "bindingconstraints.ini"
    )
    assert len(bd_config) == 1
    assert bd_config.get("0") == {
        "name": "BD 2",
        "id": "bd 2",
        "enabled": False,
        "area1.cluster": 50.0,
        "operator": "both",
        "type": "daily",
    }


def test_match(command_context: CommandContext):
    base = CreateBindingConstraint(
        name="foo",
        enabled=False,
        time_step=TimeStep.DAILY,
        operator=BindingConstraintOperator.BOTH,
        coeffs={"a": [0.3]},
        values=[[0]],
        command_context=command_context,
    )
    other_match = CreateBindingConstraint(
        name="foo",
        enabled=False,
        time_step=TimeStep.DAILY,
        operator=BindingConstraintOperator.BOTH,
        coeffs={"a": [0.3]},
        values=[[0]],
        command_context=command_context,
    )
    other_not_match = CreateBindingConstraint(
        name="bar",
        enabled=False,
        time_step=TimeStep.DAILY,
        operator=BindingConstraintOperator.BOTH,
        coeffs={"a": [0.3]},
        command_context=command_context,
    )
    other_other = RemoveArea(id="id", command_context=command_context)
    assert base.match(other_match)
    assert not base.match(other_not_match)
    assert not base.match(other_other)
    assert base.match_signature() == "create_binding_constraint%foo"
    assert base.get_inner_matrices() == ["matrix_id"]

    base = UpdateBindingConstraint(
        id="foo",
        enabled=False,
        time_step=TimeStep.DAILY,
        operator=BindingConstraintOperator.BOTH,
        coeffs={"a": [0.3]},
        values=[[0]],
        command_context=command_context,
    )
    other_match = UpdateBindingConstraint(
        id="foo",
        enabled=False,
        time_step=TimeStep.DAILY,
        operator=BindingConstraintOperator.BOTH,
        coeffs={"a": [0.3]},
        values=[[0]],
        command_context=command_context,
    )
    other_not_match = UpdateBindingConstraint(
        id="bar",
        enabled=False,
        time_step=TimeStep.DAILY,
        operator=BindingConstraintOperator.BOTH,
        coeffs={"a": [0.3]},
        command_context=command_context,
    )
    other_other = RemoveArea(id="id", command_context=command_context)
    assert base.match(other_match)
    assert not base.match(other_not_match)
    assert not base.match(other_other)
    assert base.match_signature() == "update_binding_constraint%foo"
    assert base.get_inner_matrices() == ["matrix_id"]

    base = RemoveBindingConstraint(id="foo", command_context=command_context)
    other_match = RemoveBindingConstraint(
        id="foo", command_context=command_context
    )
    other_not_match = RemoveBindingConstraint(
        id="bar", command_context=command_context
    )
    other_other = RemoveLink(
        area1="id", area2="id2", command_context=command_context
    )
    assert base.match(other_match)
    assert not base.match(other_not_match)
    assert not base.match(other_other)
    assert base.match_signature() == "remove_binding_constraint%foo"
    assert base.get_inner_matrices() == []


def test_revert(command_context: CommandContext):
    base = CreateBindingConstraint(
        name="foo",
        enabled=False,
        time_step=TimeStep.DAILY,
        operator=BindingConstraintOperator.BOTH,
        coeffs={"a": [0.3]},
        values=[[0]],
        command_context=command_context,
    )
    assert CommandReverter().revert(base, [], None) == [
        RemoveBindingConstraint(id="foo", command_context=command_context)
    ]

    base = UpdateBindingConstraint(
        id="foo",
        enabled=False,
        time_step=TimeStep.DAILY,
        operator=BindingConstraintOperator.BOTH,
        coeffs={"a": [0.3]},
        values=[[0]],
        command_context=command_context,
    )
    mock_command_extractor = Mock(spec=CommandExtractor)
    object.__setattr__(
        base,
        "_get_command_extractor",
        Mock(return_value=mock_command_extractor),
    )
    assert CommandReverter().revert(
        base,
        [
            UpdateBindingConstraint(
                id="foo",
                enabled=True,
                time_step=TimeStep.WEEKLY,
                operator=BindingConstraintOperator.BOTH,
                coeffs={"a": [0.3]},
                values=[[0]],
                command_context=command_context,
            ),
            UpdateBindingConstraint(
                id="foo",
                enabled=True,
                time_step=TimeStep.HOURLY,
                operator=BindingConstraintOperator.BOTH,
                coeffs={"a": [0.3]},
                values=[[0]],
                command_context=command_context,
            ),
        ],
        None,
    ) == [
        UpdateBindingConstraint(
            id="foo",
            enabled=True,
            time_step=TimeStep.HOURLY,
            operator=BindingConstraintOperator.BOTH,
            coeffs={"a": [0.3]},
            values=[[0]],
            command_context=command_context,
        )
    ]
    assert CommandReverter().revert(
        base,
        [
            UpdateBindingConstraint(
                id="foo",
                enabled=True,
                time_step=TimeStep.WEEKLY,
                operator=BindingConstraintOperator.BOTH,
                coeffs={"a": [0.3]},
                values=[[0]],
                command_context=command_context,
            ),
            CreateBindingConstraint(
                name="foo",
                enabled=True,
                time_step=TimeStep.HOURLY,
                operator=BindingConstraintOperator.EQUAL,
                coeffs={"a": [0.3]},
                values=[[0]],
                command_context=command_context,
            ),
        ],
        None,
    ) == [
        UpdateBindingConstraint(
            id="foo",
            enabled=True,
            time_step=TimeStep.HOURLY,
            operator=BindingConstraintOperator.EQUAL,
            coeffs={"a": [0.3]},
            values="matrix_id",
            comments=None,
            command_context=command_context,
        )
    ]
    study = FileStudy(config=Mock(), tree=Mock())
    CommandReverter().revert(base, [], study)
    mock_command_extractor.extract_binding_constraint.assert_called_with(
        study, "foo"
    )

    base = RemoveBindingConstraint(id="foo", command_context=command_context)
    mock_command_extractor = Mock(spec=CommandExtractor)
    object.__setattr__(
        base,
        "_get_command_extractor",
        Mock(return_value=mock_command_extractor),
    )
    assert CommandReverter().revert(
        base,
        [
            UpdateBindingConstraint(
                id="foo",
                enabled=True,
                time_step=TimeStep.WEEKLY,
                operator=BindingConstraintOperator.BOTH,
                coeffs={"a": [0.3]},
                values=[[0]],
                command_context=command_context,
            ),
            CreateBindingConstraint(
                name="foo",
                enabled=True,
                time_step=TimeStep.HOURLY,
                operator=BindingConstraintOperator.EQUAL,
                coeffs={"a": [0.3]},
                values=[[0]],
                command_context=command_context,
            ),
        ],
        None,
    ) == [
        CreateBindingConstraint(
            name="foo",
            enabled=True,
            time_step=TimeStep.HOURLY,
            operator=BindingConstraintOperator.EQUAL,
            coeffs={"a": [0.3]},
            command_context=command_context,
        )
    ]
    mock_command_extractor.extract_binding_constraint.side_effect = (
        ChildNotFoundError("")
    )
    CommandReverter().revert(base, [], study)
    mock_command_extractor.extract_binding_constraint.assert_called_with(
        study, "foo"
    )


def test_create_diff(command_context: CommandContext):
    base = CreateBindingConstraint(
        name="foo",
        enabled=False,
        time_step=TimeStep.DAILY,
        operator=BindingConstraintOperator.BOTH,
        coeffs={"a": [0.3]},
        values="a",
        command_context=command_context,
    )
    other_match = CreateBindingConstraint(
        name="foo",
        enabled=True,
        time_step=TimeStep.HOURLY,
        operator=BindingConstraintOperator.EQUAL,
        coeffs={"b": [0.3]},
        values="b",
        command_context=command_context,
    )
    assert base.create_diff(other_match) == [
        UpdateBindingConstraint(
            id="foo",
            enabled=True,
            time_step=TimeStep.HOURLY,
            operator=BindingConstraintOperator.EQUAL,
            coeffs={"b": [0.3]},
            values="b",
            command_context=command_context,
        )
    ]

    base = UpdateBindingConstraint(
        id="foo",
        enabled=False,
        time_step=TimeStep.DAILY,
        operator=BindingConstraintOperator.BOTH,
        coeffs={"a": [0.3]},
        values=[[0]],
        command_context=command_context,
    )
    other_match = UpdateBindingConstraint(
        id="foo",
        enabled=False,
        time_step=TimeStep.DAILY,
        operator=BindingConstraintOperator.BOTH,
        coeffs={"a": [0.3]},
        values=[[0]],
        command_context=command_context,
    )
    assert base.create_diff(other_match) == [other_match]

    base = RemoveBindingConstraint(id="foo", command_context=command_context)
    other_match = RemoveBindingConstraint(
        id="foo", command_context=command_context
    )
    assert base.create_diff(other_match) == []
