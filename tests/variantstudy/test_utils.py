from antarest.study.storage.variantstudy.business.utils import (
    transform_command_to_dto,
)
from antarest.study.storage.variantstudy.model.command.create_area import (
    CreateArea,
)
from antarest.study.storage.variantstudy.model.command.create_link import (
    CreateLink,
)
from antarest.study.storage.variantstudy.model.command_context import (
    CommandContext,
)
from antarest.study.storage.variantstudy.model.model import CommandDTO


def test_aggregate_commands(command_context: CommandContext):
    command_list = [
        CreateArea(area_name="a", command_context=command_context),
        CreateArea(area_name="b", command_context=command_context),
        CreateLink(area1="a", area2="b", command_context=command_context),
        CreateArea(area_name="d", command_context=command_context),
        CreateArea(area_name="e", command_context=command_context),
    ]
    command_dto_list = transform_command_to_dto(
        command_list, force_aggregate=True
    )
    assert len(command_dto_list) == 3

    command_dto_list = transform_command_to_dto(command_list)
    assert len(command_dto_list) == 5

    command_ref_list = [
        CommandDTO(
            action="create_area", args=[{"area_name": "a"}, {"area_name": "b"}]
        ),
        CommandDTO(action="create_link", args={"area1": "a", "area2": "b"}),
        CommandDTO(action="create_area", args={"area_name": "d"}),
        CommandDTO(action="create_area", args={"area_name": "e"}),
    ]

    command_dto_list = transform_command_to_dto(command_list, command_ref_list)
    assert len(command_dto_list) == 4
