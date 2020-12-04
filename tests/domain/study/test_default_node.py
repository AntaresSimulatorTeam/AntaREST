from typing import Dict, List

import pytest

from api_iso_antares.custom_types import JSON
from api_iso_antares.domain.study.default_node import DefaultNode
from api_iso_antares.domain.study.inode import INode
from tests.domain.study.utils import TestDefaultNode, TestSubNode


def build_tree() -> INode:
    return TestDefaultNode(
        children={
            "input": TestSubNode(value=100),
            "output": TestSubNode(value=200),
        }
    )


@pytest.mark.unit_test
def test_get():
    tree = build_tree()

    res = tree.get(["input"])
    assert res == 100

    res = tree.get([])
    assert res == {"input": 100, "output": 200}


@pytest.mark.unit_test
def test_save():
    tree = build_tree()

    tree.save(105, ["output"])
    assert tree.get(["output"]) == 105

    tree.save({"input": 205})
    assert tree.get(["input"]) == 205
