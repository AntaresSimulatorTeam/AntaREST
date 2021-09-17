from typing import List, Optional, Any

from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.model.command.common import (
    CommandOutput,
    CommandName,
)
from antarest.study.storage.variantstudy.model.command.icommand import ICommand
from antarest.study.storage.variantstudy.model.command_context import (
    CommandContext,
)
from antarest.study.storage.variantstudy.model.model import CommandDTO


class CommandGroup(ICommand):
    def __init__(
        self, command_list: List[ICommand], command_context: CommandContext
    ) -> None:
        super().__init__(
            command_name=CommandName.COMMAND_GROUP,
            version=1,
            command_context=command_context,
        )
        self.command_list = command_list

    def _apply(self, study_data: FileStudy) -> CommandOutput:
        outputs: List[CommandOutput] = []
        success = True
        for command in self.command_list:
            output = command.apply(study_data)
            outputs.append(output)
            if not output.status:
                success = False
                break
        return CommandOutput(
            status=success,
            message="\n".join([output.message for output in outputs]),
        )

    def to_dto(self) -> CommandDTO:
        raise NotImplementedError()

    def match(self, other: "ICommand", equal: bool = False) -> bool:
        raise NotImplementedError()

    def revert(self, history: List["ICommand"], base: FileStudy) -> "ICommand":
        rolling_history = list(history)
        reverted_commands: List[ICommand] = []
        for command in self.command_list:
            reverted_command = command.revert(rolling_history, base)
            rolling_history.append(command)
            reverted_commands.append(reverted_command)
        return CommandGroup(
            command_list=reverted_commands,
            command_context=self.command_context,
        )
