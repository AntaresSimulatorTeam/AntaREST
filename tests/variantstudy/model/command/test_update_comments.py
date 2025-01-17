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

from unittest.mock import Mock

import pytest

from antarest.study.model import STUDY_VERSION_8_8
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.business.command_extractor import CommandExtractor
from antarest.study.storage.variantstudy.business.command_reverter import CommandReverter
from antarest.study.storage.variantstudy.model.command.remove_area import RemoveArea
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


def test_match(command_context: CommandContext):
    base = UpdateComments(comments="comments", command_context=command_context, study_version=STUDY_VERSION_8_8)
    other_match = UpdateComments(comments="comments", command_context=command_context, study_version=STUDY_VERSION_8_8)
    other_not_match = UpdateComments(
        comments="other_comments", command_context=command_context, study_version=STUDY_VERSION_8_8
    )
    other_other = RemoveArea(id="id", command_context=command_context, study_version=STUDY_VERSION_8_8)
    assert base.match(other_match)
    assert not base.match(other_not_match, equal=True)
    assert not base.match(other_other)
    assert base.match_signature() == "update_comments"


def test_revert(
    command_context: CommandContext,
    empty_study: FileStudy,
):
    mock_command_extractor = Mock(spec=CommandExtractor)
    mock_command_extractor.command_context = command_context
    mock_command_extractor.generate_update_comments.side_effect = lambda x: CommandExtractor.generate_update_comments(
        mock_command_extractor, x
    )
    study_version = empty_study.config.version
    base_command = UpdateComments(comments="comments", command_context=command_context, study_version=study_version)

    object.__setattr__(
        base_command,
        "get_command_extractor",
        Mock(return_value=mock_command_extractor),
    )

    CommandReverter().revert(base_command, [], empty_study)
    mock_command_extractor.generate_update_comments.assert_called_with(empty_study.tree)
    assert CommandReverter().revert(
        base_command,
        [UpdateComments(comments="comments", command_context=command_context, study_version=study_version)],
        empty_study,
    ) == [UpdateComments(comments="comments", command_context=command_context, study_version=study_version)]
    assert CommandReverter().revert(base_command, [], base=empty_study) == [
        UpdateComments(
            comments='<?xml version="1.0" encoding="UTF-8"?>\n<richtext version="1.0.0.0" '
            'xmlns="http://www.wxwidgets.org">\n  <paragraphlayout textcolor="#000000" fontpointsize="9" '
            'fontfamily="70" fontstyle="90" fontweight="90" fontunderlined="0" fontface="Segoe UI" '
            'alignment="1" parspacingafter="10" parspacingbefore="0" linespacing="10" margin-left="5,'
            '4098" margin-right="5,4098" margin-top="5,4098" margin-bottom="5,4098">\n    <paragraph>\n      '
            "<text></text>\n    </paragraph>\n  </paragraphlayout>\n</richtext>\n",
            command_context=command_context,
            study_version=study_version,
        )
    ]


def test_create_diff(command_context: CommandContext):
    base = UpdateComments(comments="comments", command_context=command_context, study_version=STUDY_VERSION_8_8)
    other_match = UpdateComments(comments="comments", command_context=command_context, study_version=STUDY_VERSION_8_8)
    assert base.create_diff(other_match) == [other_match]
