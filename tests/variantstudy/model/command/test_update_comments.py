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

import pytest

from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.model.command.update_comments import UpdateComments
from antarest.study.storage.variantstudy.model.command_context import CommandContext


@pytest.mark.unit_test
def test_update_comments(empty_study: FileStudy, command_context: CommandContext):
    study_path = empty_study.config.study_path
    study_version = empty_study.config.version
    comments = "comments"

    update_comments_command = UpdateComments(
        comments=comments, command_context=command_context, study_version=study_version
    )
    output = update_comments_command.apply(empty_study)
    assert output.status

    with open(study_path / "settings" / "comments.txt") as file:
        file_comments = file.read()

    assert comments == file_comments
