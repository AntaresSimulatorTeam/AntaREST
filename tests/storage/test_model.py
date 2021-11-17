from pathlib import Path

import pytest

from antarest.study.model import PatchLeaf, PatchNode, PatchLeafDict
from antarest.study.storage.rawstudy.model.filesystem.config.model import (
    FileStudyTreeConfigDTO,
    FileStudyTreeConfig,
    Area,
    Set,
    Simulation,
)


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


def test_file_study_tree_config_dto():
    config = FileStudyTreeConfig(
        study_path=Path("test"),
        path=Path("curr_path"),
        study_id="study_id",
        version=700,
        output_path=Path("output_path"),
        areas={
            "a": Area(
                name="a",
                links={},
                thermals=[],
                renewables=[],
                filters_synthesis=[],
                filters_year=[],
            )
        },
        sets={"s": Set()},
        outputs={
            "o": Simulation(
                name="o",
                date="date",
                mode="mode",
                nbyears=1,
                synthesis=True,
                by_year=True,
                error=True,
            )
        },
        bindings=["b1"],
        store_new_set=False,
        archive_input_series=["?"],
        enr_modelling="aggregated",
    )
    config_dto = FileStudyTreeConfigDTO.from_build_config(config)
    assert list(config_dto.dict().keys()) + ["cache"] == list(
        config.__dict__.keys()
    )
    assert config_dto.to_build_config() == config
