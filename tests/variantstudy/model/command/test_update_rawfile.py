import base64
import os.path
from pathlib import Path
from typing import cast

from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.model.command.common import (
    CommandName,
)
from antarest.study.storage.variantstudy.model.command.update_raw_file import (
    UpdateRawFile,
)
from antarest.study.storage.variantstudy.model.command_context import (
    CommandContext,
)
from antarest.study.storage.variantstudy.model.model import CommandDTO


def test_update_rawfile(
    empty_study: FileStudy, command_context: CommandContext
) -> None:
    data_path = Path(os.path.dirname(__file__)) / "data.png"
    data = base64.b64encode(data_path.read_bytes()).decode("utf-8")

    original_data = empty_study.tree.get(["settings", "resources", "study"])

    command = UpdateRawFile(
        target="settings/resources/study",
        b64Data=data,
        command_context=command_context,
    )

    reverted_commands = command.revert([], empty_study)
    assert cast(
        UpdateRawFile, reverted_commands[0]
    ).b64Data == base64.b64encode(original_data).decode("utf-8")

    alt_command = UpdateRawFile(
        target="settings/resources/study",
        b64Data="",
        command_context=command_context,
    )
    reverted_commands = command.revert([alt_command], empty_study)
    assert cast(UpdateRawFile, reverted_commands[0]).b64Data == ""

    assert command.match(alt_command)
    assert not command.match(alt_command, True)
    assert len(command.get_inner_matrices()) == 0
    assert [alt_command] == command.create_diff(alt_command)

    res = command.apply(empty_study)
    assert res.status
    new_data = empty_study.tree.get(["settings", "resources", "study"])
    assert original_data != new_data
    assert cast(bytes, new_data).startswith(b"\x89PNG")
