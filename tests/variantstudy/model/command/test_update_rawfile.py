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

import base64
import os.path
from pathlib import Path
from typing import cast

from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.model.command.update_raw_file import UpdateRawFile
from antarest.study.storage.variantstudy.model.command_context import CommandContext


def test_update_rawfile(empty_study_880: FileStudy, command_context: CommandContext) -> None:
    empty_study = empty_study_880
    data_path = Path(os.path.dirname(__file__)) / "data.png"
    data = base64.b64encode(data_path.read_bytes()).decode("utf-8")

    original_data = empty_study.tree.get(["settings", "resources", "study"])

    command = UpdateRawFile(
        target="settings/resources/study",
        b64Data=data,
        command_context=command_context,
        study_version=empty_study.config.version,
    )

    assert len(command.get_inner_matrices()) == 0

    res = command.apply(empty_study)
    assert res.status
    new_data = empty_study.tree.get(["settings", "resources", "study"])
    assert original_data != new_data
    assert cast(bytes, new_data).startswith(b"\x89PNG")
