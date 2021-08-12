from abc import ABC, abstractmethod

from pydantic import BaseModel

from antarest.study.storage.variantstudy.model.command.common import (
    CommandOutput,
    CommandName,
)


class ICommand(ABC, BaseModel):
    command_name: CommandName

    @abstractmethod
    def apply(self) -> CommandOutput:
        raise NotImplementedError
