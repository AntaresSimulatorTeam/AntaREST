import configparser
from unittest.mock import Mock

from checksumdir import dirhash

from antarest.matrixstore.service import MatrixService
from antarest.study.storage.rawstudy.model.filesystem.config.model import (
    transform_name_to_id,
)
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.business.default_values import (
    FilteringOptions,
    LinkProperties,
)
from antarest.study.storage.variantstudy.business.matrix_constants_generator import (
    GeneratorMatrixConstants,
)
from antarest.study.storage.variantstudy.model.command.create_area import (
    CreateArea,
)
from antarest.study.storage.variantstudy.model.command.create_link import (
    CreateLink,
)
from antarest.study.storage.variantstudy.model.command.icommand import ICommand
from antarest.study.storage.variantstudy.model.command.remove_area import (
    RemoveArea,
)
from antarest.study.storage.variantstudy.model.command.remove_link import (
    RemoveLink,
)
from antarest.study.storage.variantstudy.model.command_context import (
    CommandContext,
)


class TestRemoveLink:
    def test_validation(self, empty_study: FileStudy):
        pass

    def test_apply(
        self, empty_study: FileStudy, command_context: CommandContext
    ):
        area1 = "Area1"
        area1_id = transform_name_to_id(area1)
        area2 = "Area2"
        area2_id = transform_name_to_id(area2)

        CreateArea.parse_obj(
            {
                "area_name": area1,
                "command_context": command_context,
            }
        ).apply(empty_study)

        CreateArea.parse_obj(
            {
                "area_name": area2,
                "command_context": command_context,
            }
        ).apply(empty_study)

        hash_before_link = dirhash(empty_study.config.study_path, "md5")

        CreateLink(
            area1=area1_id,
            area2=area2_id,
            parameters={},
            command_context=command_context,
            series=[[0]],
        ).apply(empty_study)

        output = RemoveLink(
            area1=area1_id,
            area2=area2_id,
            command_context=command_context,
        ).apply(empty_study)

        assert output.status
        assert (
            dirhash(empty_study.config.study_path, "md5") == hash_before_link
        )


def test_match(command_context: CommandContext):
    base = RemoveLink(
        area1="foo", area2="bar", command_context=command_context
    )
    other_match = RemoveLink(
        area1="foo", area2="bar", command_context=command_context
    )
    other_not_match = RemoveLink(
        area1="foo", area2="baz", command_context=command_context
    )
    other_other = RemoveArea(id="id", command_context=command_context)
    assert base.match(other_match)
    assert not base.match(other_not_match)
    assert not base.match(other_other)
    assert base.match_signature() == "remove_link%foo%bar"
    assert base.get_inner_matrices() == []
