import logging
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

logger = logging.getLogger(__name__)


class ICommand(ABC, BaseModel):
    command_name: CommandName
    version: int
    command_context: CommandContext

    @abstractmethod
    def _apply(self, study_data: FileStudy) -> CommandOutput:
        raise NotImplementedError()

    def apply(self, study_data: FileStudy) -> CommandOutput:
        try:
            return self._apply(study_data)
        except Exception as e:
            logger.warning(
                f"Failed to execute variant command {self.command_name}",
                exc_info=e,
            )
            return CommandOutput(
                status=False,
                message=f"Unexpected exception occurred when trying to apply command {self.command_name}",
            )

    @abstractmethod
    def revert(self, study_data: FileStudy) -> CommandOutput:
        raise NotImplementedError()

    class Config:
        arbitrary_types_allowed = True
