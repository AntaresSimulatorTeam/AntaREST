from antarest.matrixstore.service import MatrixService
from antarest.study.storage.rawstudy.io.reader import MultipleSameKeysIniReader
from antarest.study.storage.rawstudy.model.filesystem.config.model import (
    transform_name_to_id,
)
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.business.matrix_constants_generator import (
    GeneratorMatrixConstants,
)
from antarest.study.storage.variantstudy.model.command.create_area import (
    CreateArea,
)
from antarest.study.storage.variantstudy.model.command.create_cluster import (
    CreateCluster,
)
from antarest.study.storage.variantstudy.model.command.update_config import (
    UpdateConfig,
)
from antarest.study.storage.variantstudy.model.command_context import (
    CommandContext,
)


def test_update_config(empty_study: FileStudy, matrix_service: MatrixService):
    command_context = CommandContext(
        generator_matrix_constants=GeneratorMatrixConstants(
            matrix_service=matrix_service
        ),
        matrix_service=matrix_service,
    )
    study_path = empty_study.config.study_path
    area1 = "Area1"
    area1_id = transform_name_to_id(area1)

    CreateArea.parse_obj(
        {
            "area_name": area1,
            "metadata": {},
            "command_context": command_context,
        }
    ).apply(empty_study)

    update_settings_command = UpdateConfig(
        target="settings/generaldata/optimization/simplex-range",
        data="day",
        command_context=command_context,
    )
    output = update_settings_command.apply(empty_study)
    assert output.status
    generaldata = MultipleSameKeysIniReader().read(
        study_path / "settings/generaldata.ini"
    )
    assert generaldata["optimization"]["simplex-range"] == "day"
    assert generaldata["optimization"]["transmission-capacities"]

    update_settings_command = UpdateConfig(
        target=f"input/areas/{area1_id}/optimization/nodal optimization/other-dispatchable-power",
        data=False,
        command_context=command_context,
    )
    output = update_settings_command.apply(empty_study)
    assert output.status
    area_config = MultipleSameKeysIniReader().read(
        study_path / f"input/areas/{area1_id}/optimization.ini"
    )
    assert not area_config["nodal optimization"]["other-dispatchable-power"]
