from abc import ABC, abstractmethod
from typing import Optional

from pydantic import BaseModel

from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.model.command.common import (
    CommandOutput,
    CommandName,
)
from antarest.study.storage.variantstudy.model.command_context import (
    CommandContext,
)


class ICommand(ABC, BaseModel):
    command_name: CommandName
    version: int
    command_context: Optional[CommandContext] = None

    @abstractmethod
    def apply(self, study_data: FileStudy) -> CommandOutput:
        raise NotImplementedError()

    @abstractmethod
    def revert(self, study_data: FileStudy) -> CommandOutput:
        raise NotImplementedError()

    class Config:
        arbitrary_types_allowed = True
