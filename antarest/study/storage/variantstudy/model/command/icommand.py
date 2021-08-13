from abc import ABC, abstractmethod

from pydantic import BaseModel

from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.model.command.common import (
    CommandOutput,
    CommandName,
)


class ICommand(ABC, BaseModel):
    command_name: CommandName
    version: int

    @abstractmethod
    def apply(self, study_data: FileStudy) -> CommandOutput:
        raise NotImplementedError()

    @abstractmethod
    def revert(self, study_data: FileStudy) -> CommandOutput:
        raise NotImplementedError()
