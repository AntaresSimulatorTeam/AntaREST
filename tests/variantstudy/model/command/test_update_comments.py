from unittest.mock import Mock

import pytest

from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.model.command.remove_area import (
    RemoveArea,
)
from antarest.study.storage.variantstudy.model.command.update_comments import (
    UpdateComments,
)
from antarest.study.storage.variantstudy.model.command_context import (
    CommandContext,
)


@pytest.mark.unit_test
def test_update_comments(
    empty_study: FileStudy, command_context: CommandContext
):
    study_path = empty_study.config.study_path
    comments = "comments"

    update_comments_command = UpdateComments(
        comments=comments,
        command_context=command_context,
    )
    output = update_comments_command.apply(empty_study)
    assert output.status

    with open(study_path / "settings" / "comments.txt") as file:
        file_comments = file.read()

    assert comments == file_comments


def test_match(command_context: CommandContext):
    base = UpdateComments(comments="comments", command_context=command_context)
    other_match = UpdateComments(
        comments="comments", command_context=command_context
    )
    other_not_match = UpdateComments(
        comments="other_comments", command_context=command_context
    )
    other_other = RemoveArea(id="id", command_context=command_context)
    assert base.match(other_match)
    assert not base.match(other_not_match, equal=True)
    assert not base.match(other_other)
    assert base.match_signature() == "update_comments%comments"


def test_revert(command_context: CommandContext):
    base = UpdateComments(comments="comments", command_context=command_context)
    study = FileStudy(config=Mock(), tree=Mock())
    base.revert([], study)
    base.command_context.command_extractor.generate_update_comments.assert_called_with(
        study.tree
    )
    assert (
        base.revert(
            [
                UpdateComments(
                    comments="comments", command_context=command_context
                )
            ],
            study,
        )
        == [
            UpdateComments(
                comments="comments", command_context=command_context
            )
        ]
    )
    assert base.revert([]) == [
        UpdateComments(comments="", command_context=command_context)
    ]


def test_create_diff(command_context: CommandContext):
    base = UpdateComments(comments="comments", command_context=command_context)
    other_match = UpdateComments(
        comments="comments", command_context=command_context
    )
    assert base.create_diff(other_match) == [other_match]
