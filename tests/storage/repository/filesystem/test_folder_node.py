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

import json
import textwrap
import typing as t
from pathlib import Path
from unittest.mock import Mock

import pytest

from antarest.core.exceptions import ChildNotFoundError
from antarest.study.storage.rawstudy.model.filesystem.config.model import FileStudyTreeConfig
from antarest.study.storage.rawstudy.model.filesystem.factory import StudyFactory
from antarest.study.storage.rawstudy.model.filesystem.ini_file_node import IniFileNode
from antarest.study.storage.rawstudy.model.filesystem.inode import INode
from antarest.study.storage.rawstudy.model.filesystem.raw_file_node import RawFileNode
from antarest.study.storage.rawstudy.model.filesystem.root.input.areas.list import InputAreasList
from tests.storage.repository.filesystem.utils import CheckSubNode, TestMiddleNode


def build_tree() -> INode[t.Any, t.Any, t.Any]:
    config = Mock()
    config.path.exist.return_value = True
    config.archive_path = None
    return TestMiddleNode(
        matrix_mapper=Mock(),
        config=config,
        children={
            "input": CheckSubNode(config, value=100),
            "output": CheckSubNode(config, value=200),
        },
    )


@pytest.mark.unit_test
def test_get() -> None:
    tree = build_tree()

    res = tree.get(["input"])
    assert res == 100

    res = tree.get()
    assert res == {"input": 100, "output": 200}


@pytest.mark.unit_test
def test_get_input_areas_sets(tmp_path: Path) -> None:
    """
    Read the content of the `sets.ini` file in the `input/areas` directory.
    The goal of this test is to verify the behavior of the `get` method of the `FileStudyTree` class
    for the case where the subdirectories or the INI file do not exist.
    """

    matrix_mapper_factory = Mock()
    matrix_mapper_factory.create.return_value = Mock()

    study_factory = StudyFactory(matrix_mapper_factory=matrix_mapper_factory, cache=Mock())
    study_id = "c5633166-afe1-4ce5-9305-75bc2779aad6"

    file_study = study_factory.create_from_fs(path=tmp_path, with_matrix_normalization=True, study_id=study_id, use_cache=False)
    url = ["input", "areas", "sets"]  # sets.ini

    # Empty study tree structure
    actual = file_study.tree.get(url)
    assert actual == {}

    # Add the "settings" directory
    tmp_path.joinpath("input").mkdir()
    actual = file_study.tree.get(url)
    assert actual == {}

    # Add the "areas" directory
    tmp_path.joinpath("input/areas").mkdir()
    actual = file_study.tree.get(url)
    assert actual == {}

    # Add the "sets.ini" file
    sets = textwrap.dedent(
        """\
        [all areas]
        caption = All areas
        comments = Spatial aggregates on all areas
        output = false
        apply-filter = add-all
        """
    )
    tmp_path.joinpath("input/areas/sets.ini").write_text(sets)
    actual = file_study.tree.get(url)
    expected = {
        "all areas": {
            "caption": "All areas",
            "comments": "Spatial aggregates on all areas",
            "output": False,
            "apply-filter": "add-all",
        }
    }
    assert actual == expected


@pytest.mark.unit_test
def test_get_user_expansion_sensitivity_sensitivity_in(tmp_path: Path) -> None:
    """
    Read the content of the `sensitivity_in.json` file in the `user/expansion/sensitivity` directory.
    The goal of this test is to verify the behavior of the `get` method of the `FileStudyTree` class
    for the case where the subdirectories or the JSON file do not exist.
    """
    matrix_mapper_factory = Mock()
    matrix_mapper_factory.create.return_value = Mock()

    study_factory = StudyFactory(matrix_mapper_factory=matrix_mapper_factory, cache=Mock())
    study_id = "616ac707-c108-47af-9e02-c37cc043511a"
    file_study = study_factory.create_from_fs(tmp_path, with_matrix_normalization=True, study_id=study_id, use_cache=False)

    url = ["user", "expansion", "sensitivity", "sensitivity_in"]

    # Empty study tree structure
    # fixme: bad error message
    with pytest.raises(ChildNotFoundError, match=r"'expansion' not a child of User"):
        file_study.tree.get(url)

    # Add the "user" directory
    tmp_path.joinpath("user").mkdir()
    with pytest.raises(ChildNotFoundError, match=r"'expansion' not a child of User"):
        file_study.tree.get(url)

    # Add the "expansion" directory
    tmp_path.joinpath("user/expansion").mkdir()
    with pytest.raises(ChildNotFoundError, match=r"'sensitivity' not a child of Expansion"):
        file_study.tree.get(url)

    # Add the "sensitivity" directory
    tmp_path.joinpath("user/expansion/sensitivity").mkdir()
    actual = file_study.tree.get(url)
    assert actual == {}

    # Add the "sensitivity_in.json" file
    sensitivity_obj = {"epsilon": 10000.0, "projection": ["pv", "battery"], "capex": True}
    tmp_path.joinpath("user/expansion/sensitivity/sensitivity_in.json").write_text(json.dumps(sensitivity_obj))
    actual_obj = file_study.tree.get(url)
    assert actual_obj == sensitivity_obj


@pytest.mark.unit_test
def test_get_depth() -> None:
    config = Mock()
    config.path.exist.return_value = True
    tree = TestMiddleNode(
        matrix_mapper=Mock(),
        config=config,
        children={"childA": build_tree(), "childB": build_tree()},
    )

    expected: t.Dict[str, t.Dict[str, t.Any]] = {
        "childA": {},
        "childB": {},
    }

    assert tree.get(depth=1) == expected


def test_validate() -> None:
    config = Mock()
    config.path.exist.return_value = True
    tree = TestMiddleNode(
        matrix_mapper=Mock(),
        config=config,
        children={"childA": build_tree(), "childB": build_tree()},
    )

    assert tree.check_errors(data={"wrongChild": {}}) == [
        "key=wrongChild not in ['childA', 'childB'] for TestMiddleNode"
    ]
    with pytest.raises(ValueError):
        tree.check_errors(data={"wrongChild": {}}, raising=True)

    assert tree.check_errors(data={"wrongChild": {}}, url=["childA"]) == [
        "key=wrongChild not in ['input', 'output'] for TestMiddleNode"
    ]

    assert tree.check_errors(data={"childA": {"input": 42, "output": 42}}) == []


@pytest.mark.unit_test
def test_save() -> None:
    tree = build_tree()

    tree.save(105, ["output"])
    assert tree.get(["output"]) == 105

    tree.save({"input": 205})
    assert tree.get(["input"]) == 205


@pytest.mark.unit_test
def test_filter() -> None:
    tree = build_tree()

    expected_json = {
        "input": 100,
        "output": 200,
    }

    assert tree.get(["input,output", "value"]) == expected_json
    assert tree.get(["*", "value"]) == expected_json


def test_delete(tmp_path: Path) -> None:
    folder_node = tmp_path / "folder_node"
    folder_node.mkdir()
    sub_folder = folder_node / "sub_folder"
    sub_folder.mkdir()
    area_list = sub_folder / "area_list.ini"
    area_list.touch()
    ini_node1 = sub_folder / "ini_node1.txt"
    ini_node1.touch()
    ini_node2 = sub_folder / "ini_node2.txt"
    ini_node2.touch()
    data_node = sub_folder / "data.txt"
    data_node.touch()
    data_link_node = sub_folder / "data_link.txt"
    data_link_node.touch()

    assert area_list.exists()
    assert ini_node1.exists()
    assert ini_node2.exists()
    assert data_node.exists()
    assert data_link_node.exists()
    assert folder_node.exists()
    assert sub_folder.exists()

    config = FileStudyTreeConfig(study_path=tmp_path, path=folder_node, study_id="-1", version=-1)
    tree_node = TestMiddleNode(
        matrix_mapper=Mock(),
        config=config,
        children={
            "sub_folder": TestMiddleNode(
                matrix_mapper=Mock(),
                config=config.next_file("sub_folder"),
                children={
                    "ini_node1": IniFileNode(
                        config=config.next_file("sub_folder").next_file("ini_node1.txt"),
                        types={},
                    ),
                    "ini_node2": IniFileNode(
                        config=config.next_file("sub_folder").next_file("ini_node2.txt"),
                        types={},
                    ),
                    "area_list": InputAreasList(
                        matrix_mapper=Mock(),
                        config=config.next_file("sub_folder").next_file("area_list.ini"),
                    ),
                    "data_node": RawFileNode(
                        matrix_mapper=Mock(),
                        config=config.next_file("sub_folder").next_file("data.txt"),
                    ),
                    "data_link_node": RawFileNode(
                        matrix_mapper=Mock(),
                        config=config.next_file("sub_folder").next_file("data_link.txt"),
                    ),
                },
            ),
        },
    )

    tree_node.delete(["sub_folder", "area_list"])
    assert not area_list.exists()
    tree_node.delete(["sub_folder", "ini_node1"])
    assert not ini_node1.exists()
    tree_node.delete(["sub_folder", "data_node"])
    assert not data_node.exists()
    tree_node.delete(["sub_folder", "data_link_node"])
    assert not data_link_node.exists()
    tree_node.delete()
    assert not folder_node.exists()
