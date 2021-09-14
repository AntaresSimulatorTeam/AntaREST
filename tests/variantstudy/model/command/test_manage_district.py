from unittest.mock import Mock

from antarest.matrixstore.service import MatrixService
from antarest.study.storage.rawstudy.io.reader import MultipleSameKeysIniReader
from antarest.study.storage.rawstudy.model.filesystem.config.files import (
    ConfigPathBuilder,
)
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
from antarest.study.storage.variantstudy.model.command.create_district import (
    CreateDistrict,
    DistrictBaseFilter,
)
from antarest.study.storage.variantstudy.model.command.icommand import ICommand
from antarest.study.storage.variantstudy.model.command.remove_district import (
    RemoveDistrict,
)
from antarest.study.storage.variantstudy.model.command_context import (
    CommandContext,
)


def test_manage_district(
    empty_study: FileStudy, matrix_service: MatrixService
):
    command_context = CommandContext(
        generator_matrix_constants=GeneratorMatrixConstants(
            matrix_service=matrix_service
        ),
        matrix_service=matrix_service,
    )
    study_path = empty_study.config.study_path
    area1 = "Area1"
    area1_id = transform_name_to_id(area1)

    area2 = "Area2"
    area2_id = transform_name_to_id(area2)

    area3 = "Area3"
    area3_id = transform_name_to_id(area3)

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

    CreateArea.parse_obj(
        {
            "area_name": area3,
            "metadata": {},
            "command_context": command_context,
        }
    ).apply(empty_study)

    command_context = CommandContext(
        matrix_service=matrix_service,
        generator_matrix_constants=Mock(spec=GeneratorMatrixConstants),
    )

    create_district1_command: ICommand = CreateDistrict(
        name="Two added zone",
        metadata={},
        filter_items=[area1_id, area2_id],
        comments="First district",
        command_context=command_context,
    )
    output_d1 = create_district1_command.apply(
        study_data=empty_study,
    )
    assert output_d1.status
    sets_config = MultipleSameKeysIniReader(["+", "-"]).read(
        empty_study.config.study_path / "input/areas/sets.ini"
    )
    set_config = sets_config.get("two added zone")
    assert set(set_config["+"]) == {area1_id, area2_id}
    assert set_config["output"]
    assert set_config["comments"] == "First district"

    create_district2_command: ICommand = CreateDistrict(
        name="One substracted zone",
        metadata={},
        base_filter=DistrictBaseFilter.add_all,
        filter_items=[area1_id],
        command_context=command_context,
    )
    output_d2 = create_district2_command.apply(
        study_data=empty_study,
    )
    assert output_d2.status
    sets_config = MultipleSameKeysIniReader(["+", "-"]).read(
        empty_study.config.study_path / "input/areas/sets.ini"
    )
    set_config = sets_config.get("one substracted zone")
    assert set_config["-"] == [area1_id]
    assert set_config["apply-filter"] == "add-all"

    create_district3_command: ICommand = CreateDistrict(
        name="Empty district without output",
        metadata={},
        output=False,
        command_context=command_context,
    )
    output_d3 = create_district3_command.apply(
        study_data=empty_study,
    )
    assert output_d3.status
    assert output_d2.status
    sets_config = MultipleSameKeysIniReader(["+", "-"]).read(
        empty_study.config.study_path / "input/areas/sets.ini"
    )
    set_config = sets_config.get("empty district without output")
    assert not set_config["output"]

    output_d3 = create_district3_command.apply(
        study_data=empty_study,
    )
    assert not output_d3.status

    read_config = ConfigPathBuilder.build(empty_study.config.study_path, "")
    assert len(read_config.sets.keys()) == 4

    remove_district3_command: ICommand = RemoveDistrict(
        id="empty district without output", command_context=command_context
    )
    sets_config = MultipleSameKeysIniReader(["+", "-"]).read(
        empty_study.config.study_path / "input/areas/sets.ini"
    )
    assert len(sets_config.keys()) == 4
    remove_output_d3 = remove_district3_command.apply(
        study_data=empty_study,
    )
    assert remove_output_d3.status
    sets_config = MultipleSameKeysIniReader(["+", "-"]).read(
        empty_study.config.study_path / "input/areas/sets.ini"
    )
    assert len(sets_config.keys()) == 3
