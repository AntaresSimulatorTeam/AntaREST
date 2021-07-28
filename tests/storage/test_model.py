import pytest

from antarest.study.model import PatchLeaf, PatchNode, PatchLeafDict


@pytest.mark.unit_test
def test_patch_leaf():
    old_patch_leaf = PatchLeaf()
    old_patch_leaf.attribute1 = "value"
    old_patch_leaf.attribute2 = None
    old_patch_leaf.attribute3 = "value"
    new_patch_leaf = PatchLeaf()
    new_patch_leaf.attribute1 = "other value"
    new_patch_leaf.attribute2 = "other value"
    new_patch_leaf.attribute3 = None

    merged_patch_leaf = old_patch_leaf.patch(new_patch_leaf)
    assert merged_patch_leaf.attribute1 == new_patch_leaf.attribute1
    assert merged_patch_leaf.attribute2 == new_patch_leaf.attribute2
    assert merged_patch_leaf.attribute3 == old_patch_leaf.attribute3


@pytest.mark.unit_test
def test_patch_node():
    patch_leaf1 = PatchLeaf()
    patch_leaf1.attribute1 = "value"

    patch_leaf2 = PatchLeaf()
    patch_leaf2.attribute1 = "other value"

    old_patch_node = PatchNode()
    old_patch_node.leaf1 = patch_leaf1
    old_patch_node.leaf2 = None
    old_patch_node.leaf3 = patch_leaf1
    old_patch_node.dict_leaf = PatchLeafDict(
        {"leaf1": patch_leaf1, "leaf2": patch_leaf1}
    )

    new_patch_node = PatchNode()
    new_patch_node.leaf1 = patch_leaf2
    new_patch_node.leaf2 = patch_leaf2
    new_patch_node.leaf3 = None
    new_patch_node.dict_leaf = PatchLeafDict(
        {"leaf1": patch_leaf2, "leaf3": patch_leaf2}
    )

    merged_patch_node = old_patch_node.patch(new_patch_node)

    assert merged_patch_node.leaf1.attribute1 == patch_leaf2.attribute1
    assert merged_patch_node.leaf2 == patch_leaf2
    assert merged_patch_node.leaf3 == patch_leaf1

    assert (
        merged_patch_node.dict_leaf["leaf1"].attribute1
        == patch_leaf2.attribute1
    )
    assert merged_patch_node.dict_leaf["leaf2"] == patch_leaf1
    assert merged_patch_node.dict_leaf["leaf3"] == patch_leaf2
