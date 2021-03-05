from unittest.mock import Mock

import pytest

from antarest.storage.repository.filesystem.inode import INode
from tests.storage.repository.filesystem.utils import (
    TestSubNode,
    TestMiddleNode,
)


def build_tree() -> INode:
    config = Mock()
    config.path.exist.return_value = True
    return TestMiddleNode(
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
