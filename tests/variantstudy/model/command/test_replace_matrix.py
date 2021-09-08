from antarest.matrixstore.service import MatrixService
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.business.matrix_constants_generator import (
    GeneratorMatrixConstants,
)
from antarest.study.storage.variantstudy.model.command.create_area import (
    CreateArea,
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
        self, empty_study: FileStudy, matrix_service: MatrixService
    ):

        command_context = CommandContext(
            generator_matrix_constants=GeneratorMatrixConstants(
                matrix_service=matrix_service
            ),
            matrix_service=matrix_service,
        )
        study_path = empty_study.config.study_path
        area1 = "Area1"

        CreateArea.parse_obj(
            {
                "area_name": area1,
                "metadata": {},
                "command_context": command_context,
            }
        ).apply(empty_study)

        target_element = f"input/hydro/common/capacity/maxpower_{area1}"
        replace_matrix = ReplaceMatrix.parse_obj(
            {
                "target_element": target_element,
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
                "target_element": target_element,
                "matrix": [[0]],
                "command_context": command_context,
            }
        )
        output = replace_matrix.apply(empty_study)
        assert not output.status
