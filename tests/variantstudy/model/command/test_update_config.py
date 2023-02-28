import json
from unittest.mock import Mock, patch

import pytest

from antarest.study.storage.rawstudy.io.reader import MultipleSameKeysIniReader
from antarest.study.storage.rawstudy.model.filesystem.config.model import (
    transform_name_to_id,
)
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.rawstudy.model.filesystem.folder_node import (
    ChildNotFoundError,
)
from antarest.study.storage.variantstudy.business.command_reverter import (
    CommandReverter,
)
from antarest.study.storage.variantstudy.model.command.create_area import (
    CreateArea,
)
from antarest.study.storage.variantstudy.model.command.remove_area import (
    RemoveArea,
)
from antarest.study.storage.variantstudy.model.command.update_config import (
    UpdateConfig,
)
from antarest.study.storage.variantstudy.model.command_context import (
    CommandContext,
)


@pytest.mark.unit_test
def test_update_config(
    empty_study: FileStudy, command_context: CommandContext
):
    study_path = empty_study.config.study_path
    area1 = "Area1"
    area1_id = transform_name_to_id(area1)

    CreateArea.parse_obj(
        {
            "area_name": area1,
            "command_context": command_context,
        }
    ).apply(empty_study)

    update_settings_command = UpdateConfig(
        target="settings/generaldata/optimization/simplex-range",
        data="day",
        command_context=command_context,
    )
    output = update_settings_command.apply(empty_study)
    assert output.status
    generaldata = MultipleSameKeysIniReader().read(
        study_path / "settings/generaldata.ini"
    )
    assert generaldata["optimization"]["simplex-range"] == "day"
    assert generaldata["optimization"]["transmission-capacities"]

    update_settings_command = UpdateConfig(
        target=f"input/areas/{area1_id}/optimization/nodal optimization/other-dispatchable-power",
        data=False,
        command_context=command_context,
    )
    output = update_settings_command.apply(empty_study)
    assert output.status
    area_config = MultipleSameKeysIniReader().read(
        study_path / f"input/areas/{area1_id}/optimization.ini"
    )
    assert not area_config["nodal optimization"]["other-dispatchable-power"]

    # test UpdateConfig with byte object which is necessary with the API PUT /v1/studies/{uuid}/raw
    data = json.dumps({"first_layer": {"0": "Nothing"}}).encode("utf-8")
    command = UpdateConfig(
        target="layers/layers",
        data=data,
        command_context=command_context,
    )
    command.apply(empty_study)
    layers = MultipleSameKeysIniReader().read(study_path / "layers/layers.ini")
    assert layers == {"first_layer": {"0": "Nothing"}}
    new_data = json.dumps({"1": False}).encode("utf-8")
    command = UpdateConfig(
        target="layers/layers/first_layer",
        data=new_data,
        command_context=command_context,
    )
    command.apply(empty_study)
    layers = MultipleSameKeysIniReader().read(study_path / "layers/layers.ini")
    assert layers == {"first_layer": {"1": False}}


def test_match(command_context: CommandContext):
    base = UpdateConfig(
        target="foo", data="bar", command_context=command_context
    )
    other_match = UpdateConfig(
        target="foo", data="bar", command_context=command_context
    )
    other_not_match = UpdateConfig(
        target="hello", data="bar", command_context=command_context
    )
    other_other = RemoveArea(id="id", command_context=command_context)
    assert base.match(other_match)
    assert not base.match(other_not_match)
    assert not base.match(other_other)
    assert base.match_signature() == "update_config%foo"


@patch(
    "antarest.study.storage.variantstudy.business.command_extractor.CommandExtractor.generate_update_config"
)
def test_revert(mock_generate_update_config, command_context: CommandContext):
    base = UpdateConfig(
        target="foo", data="bar", command_context=command_context
    )
    study = FileStudy(config=Mock(), tree=Mock())
    mock_generate_update_config.side_effect = ChildNotFoundError("")
    res = CommandReverter().revert(base, [], study)
    mock_generate_update_config.assert_called_with(study.tree, ["foo"])
    assert res == []

    assert CommandReverter().revert(
        base,
        [
            UpdateConfig(
                target="foo", data="baz", command_context=command_context
            )
        ],
        study,
    ) == [
        UpdateConfig(target="foo", data="baz", command_context=command_context)
    ]


def test_create_diff(command_context: CommandContext):
    base = UpdateConfig(
        target="foo", data="bar", command_context=command_context
    )
    other_match = UpdateConfig(
        target="foo", data="baz", command_context=command_context
    )
    assert base.create_diff(other_match) == [other_match]
