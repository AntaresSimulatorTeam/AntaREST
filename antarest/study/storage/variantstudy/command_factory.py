from typing import List

from antarest.core.custom_types import JSON
from antarest.study.storage.variantstudy.model import (
    CommandDTO,
    Command,
    ICommand,
)
from antarest.study.storage.variantstudy.model.command.common import (
    CommandName,
)
from antarest.study.storage.variantstudy.model.command.create_area import (
    CreateArea,
)
from antarest.study.storage.variantstudy.model.command.update_area import (
    UpdateArea,
)


class CommandFactory:
    """
    Service to convert CommendDTO to Command
    """

    def to_command(self, command_dto: CommandDTO) -> List[ICommand]:

        if command_dto.action == CommandName.CREATE_AREA:
            if isinstance(args := command_dto.args, JSON):
                return [
                    CreateArea(
                        area_name=args["area_name"], metadata=args["metadata"]
                    )
                ]
            else:
                return [
                    CreateArea(
                        area_name=args["area_name"], metadata=args["metadata"]
                    )
                    for args in command_dto.args
                ]
        elif command_dto.action == CommandName.UPDATE_AREA:
            if isinstance(args := command_dto.args, JSON):
                return [
                    UpdateArea(
                        id=args["id"],
                        name=args["name"],
                        metadata=args["metadata"],
                    )
                ]
            else:
                return [
                    UpdateArea(
                        id=args["id"],
                        name=args["name"],
                        metadata=args["metadata"],
                    )
                    for args in command_dto.args
                ]
