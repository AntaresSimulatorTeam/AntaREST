from typing import Dict, List

import pytest

from api_iso_antares.custom_types import JSON
from api_iso_antares.domain.study.default_node import DefaultNode
from api_iso_antares.domain.study.inode import INode
from tests.domain.study.utils import TestDefaultNode, TestSubNode


def build_tree() -> INode:
    return TestDefaultNode(
        children={
            "input": TestSubNode(return_value={"data": "input"}),
            "output": TestSubNode(return_value={"data": "output"}),
        }
    )


@pytest.mark.unit_test
def test_get():
    tree = build_tree()

    res = tree.get(["input"])
    assert res == {"data": "input"}

    res = tree.get([])
    assert res == {"input": {"data": "input"}, "output": {"data": "output"}}
