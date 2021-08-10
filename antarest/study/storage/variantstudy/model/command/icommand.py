from abc import ABC, abstractmethod

from pydantic import BaseModel

from antarest.study.storage.variantstudy.model.command.common import CommandOutput


class ICommand(ABC, BaseModel):
    command_name: str

    @abstractmethod
    def apply(self) -> CommandOutput:
        raise NotImplementedError
