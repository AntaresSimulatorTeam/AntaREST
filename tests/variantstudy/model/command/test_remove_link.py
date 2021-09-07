import configparser
from unittest.mock import Mock

from checksumdir import dirhash

from antarest.matrixstore.service import MatrixService
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
        self, empty_study: FileStudy, matrix_service: MatrixService
    ):

        command_context = CommandContext(
            generator_matrix_constants=GeneratorMatrixConstants(
                matrix_service=matrix_service
            ),
            matrix_service=matrix_service,
        )
        area1 = "Area1"
        area2 = "Area2"

        CreateArea.parse_obj(
            {
                "area_name": area1,
                "metadata": {},
                "command_context": command_context,
            }
        ).apply(empty_study)

        CreateArea.parse_obj(
            {
                "area_name": area2,
                "metadata": {},
                "command_context": command_context,
            }
        ).apply(empty_study)

        hash_before_link = dirhash(empty_study.config.study_path, "md5")

        command_context = CommandContext(
            matrix_service=matrix_service,
            generator_matrix_constants=Mock(spec=GeneratorMatrixConstants),
        )

        CreateLink(
            area1=area1,
            area2=area2,
            parameters={},
            command_context=command_context,
            series=[[0]],
        ).apply(empty_study)

        output = RemoveLink(
            area1=area1,
            area2=area2,
            command_context=command_context,
        ).apply(empty_study)

        assert output.status
        assert (
            dirhash(empty_study.config.study_path, "md5") == hash_before_link
        )
