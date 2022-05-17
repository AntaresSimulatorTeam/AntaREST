from unittest.mock import Mock, patch

from antarest.study.storage.rawstudy.model.filesystem.config.model import (
    transform_name_to_id,
)
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.business.command_reverter import (
    CommandReverter,
)
from antarest.study.storage.variantstudy.model.command.create_area import (
    CreateArea,
)
from antarest.study.storage.variantstudy.model.command.remove_area import (
    RemoveArea,
)
from antarest.study.storage.variantstudy.model.command.replace_matrix import (
    ReplaceMatrix,
)
from antarest.study.storage.variantstudy.model.command_context import (
    CommandContext,
)


class TestReplaceMatrix:
    def test_validation(self, empty_study: FileStudy):
        pass

    def test_apply(
        self, empty_study: FileStudy, command_context: CommandContext
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

        target_element = f"input/hydro/common/capacity/maxpower_{area1_id}"
        replace_matrix = ReplaceMatrix.parse_obj(
            {
                "target": target_element,
                "matrix": [[0]],
                "command_context": command_context,
            }
        )
        output = replace_matrix.apply(empty_study)
        assert output.status

        assert (
            "matrix_id"
            in (study_path / (target_element + ".txt.link")).read_text()
        )

        target_element = "fake/matrix/path"
        replace_matrix = ReplaceMatrix.parse_obj(
            {
                "target": target_element,
                "matrix": [[0]],
                "command_context": command_context,
            }
        )
        output = replace_matrix.apply(empty_study)
        assert not output.status


def test_match(command_context: CommandContext):
    base = ReplaceMatrix(
        target="foo", matrix=[[0]], command_context=command_context
    )
    other_match = ReplaceMatrix(
        target="foo", matrix=[[1]], command_context=command_context
    )
    other_not_match = ReplaceMatrix(
        target="bar", matrix=[[0]], command_context=command_context
    )
    other_other = RemoveArea(id="id", command_context=command_context)
    assert base.match(other_match)
    assert not base.match(other_not_match)
    assert not base.match(other_other)
    assert base.match_signature() == "replace_matrix%foo"
    assert base.get_inner_matrices() == ["matrix_id"]


@patch(
    "antarest.study.storage.variantstudy.business.command_extractor.CommandExtractor.generate_replace_matrix"
)
def test_revert(mock_generate_replace_matrix, command_context: CommandContext):
    base = ReplaceMatrix(
        target="foo", matrix=[[0]], command_context=command_context
    )
    study = FileStudy(config=Mock(), tree=Mock())
    CommandReverter().revert(base, [], study)
    mock_generate_replace_matrix.assert_called_with(study.tree, ["foo"])
    assert CommandReverter().revert(
        base,
        [
            ReplaceMatrix(
                target="foo", matrix="b", command_context=command_context
            )
        ],
        study,
    ) == [
        ReplaceMatrix(
            target="foo", matrix="b", command_context=command_context
        )
    ]


def test_create_diff(command_context: CommandContext):
    base = ReplaceMatrix(
        target="foo", matrix="c", command_context=command_context
    )
    other_match = ReplaceMatrix(
        target="foo", matrix="b", command_context=command_context
    )
    assert base.create_diff(other_match) == [other_match]
