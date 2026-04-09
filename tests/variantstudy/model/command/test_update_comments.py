# Copyright (c) 2026, RTE (https://www.rte-france.com)
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


from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.model.command.replace_comments import ReplaceComments
from antarest.study.storage.variantstudy.model.command_context import CommandContext
from tests.helpers import build_dao_from_file_study


def test_update_comments(empty_study_870: FileStudy, command_context: CommandContext) -> None:
    dao = build_dao_from_file_study(empty_study_870, command_context)
    study_path = empty_study_870.config.study_path
    study_version = empty_study_870.config.version
    comments = "comments"

    update_comments_command = ReplaceComments(
        comments=comments, command_context=command_context, study_version=study_version
    )
    output = update_comments_command.apply(dao)
    assert output.status

    with open(study_path / "settings" / "comments.txt") as file:
        file_comments = file.read()

    assert comments == file_comments
