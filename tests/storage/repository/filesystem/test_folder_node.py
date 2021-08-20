from pathlib import Path
from unittest.mock import Mock

import pytest

from antarest.study.storage.rawstudy.model.filesystem.config.model import (
    FileStudyTreeConfig,
)
from antarest.study.storage.rawstudy.model.filesystem.ini_file_node import (
    IniFileNode,
)
from antarest.study.storage.rawstudy.model.filesystem.inode import INode
from antarest.study.storage.rawstudy.model.filesystem.raw_file_node import (
    RawFileNode,
)
from tests.storage.repository.filesystem.utils import (
    TestSubNode,
    TestMiddleNode,
)


def build_tree() -> INode:
    config = Mock()
    config.path.exist.return_value = True
    return TestMiddleNode(
        context=Mock(),
        config=config,
        children={
            "input": TestSubNode(value=100),
            "output": TestSubNode(value=200),
        },
    )


@pytest.mark.unit_test
def test_get():
    tree = build_tree()

    res = tree.get(["input"])
    assert res == 100

    res = tree.get()
    assert res == {"input": 100, "output": 200}


@pytest.mark.unit_test
def test_get_depth():
    config = Mock()
    config.path.exist.return_value = True
    tree = TestMiddleNode(
        context=Mock(),
        config=config,
        children={"childA": build_tree(), "childB": build_tree()},
    )

    expected = {
        "childA": {},
        "childB": {},
    }

    assert tree.get(depth=1) == expected


def test_validate():
    config = Mock()
    config.path.exist.return_value = True
    tree = TestMiddleNode(
        context=Mock(),
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

    assert (
        tree.check_errors(data={"childA": {"input": 42, "output": 42}}) == []
    )


@pytest.mark.unit_test
def test_save():
    tree = build_tree()

    tree.save(105, ["output"])
    assert tree.get(["output"]) == 105

    tree.save({"input": 205})
    assert tree.get(["input"]) == 205


@pytest.mark.unit_test
def test_filter():
    tree = build_tree()

    expected_json = {
        "input": 100,
        "output": 200,
    }

    assert tree.get(["input,output", "value"]) == expected_json
    assert tree.get(["*", "value"]) == expected_json


def test_delete(tmp_path: Path):

    folder_node = tmp_path / "folder_node"
    folder_node.mkdir()
    sub_folder = folder_node / "sub_folder"
    sub_folder.mkdir()
    ini_node1 = sub_folder / "ini_node1.txt"
    ini_node1.touch()
    ini_node2 = sub_folder / "ini_node2.txt"
    ini_node2.touch()
    data_node = sub_folder / "data.txt"
    data_node.touch()
    data_link_node = sub_folder / "data_link.txt.link"
    data_link_node.touch()

    assert ini_node1.exists()
    assert ini_node2.exists()
    assert data_node.exists()
    assert data_link_node.exists()
    assert folder_node.exists()
    assert sub_folder.exists()

    config = FileStudyTreeConfig(
        study_path=tmp_path, path=folder_node, study_id=-1, version=-1
    )
    tree_node = TestMiddleNode(
        context=Mock(),
        config=config,
        children={
            "sub_folder": TestMiddleNode(
                context=Mock(),
                config=config.next_file("sub_folder"),
                children={
                    "ini_node1": IniFileNode(
                        context=Mock(),
                        config=config.next_file("sub_folder").next_file(
                            "ini_node1.txt"
                        ),
                        types={},
                    ),
                    "ini_node2": IniFileNode(
                        context=Mock(),
                        config=config.next_file("sub_folder").next_file(
                            "ini_node2.txt"
                        ),
                        types={},
                    ),
                    "data_node": RawFileNode(
                        context=Mock(),
                        config=config.next_file("sub_folder").next_file(
                            "data.txt"
                        ),
                    ),
                    "data_link_node": RawFileNode(
                        context=Mock(),
                        config=config.next_file("sub_folder").next_file(
                            "data_link.txt"
                        ),
                    ),
                },
            ),
        },
    )

    tree_node.delete(["sub_folder", "ini_node1"])
    assert not ini_node1.exists()
    tree_node.delete(["sub_folder", "data_node"])
    assert not data_node.exists()
    tree_node.delete(["sub_folder", "data_link_node"])
    assert not data_link_node.exists()
    tree_node.delete()
    assert not folder_node.exists()
