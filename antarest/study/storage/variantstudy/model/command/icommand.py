import logging
from abc import ABC, abstractmethod
from typing import List, Tuple, Dict, Any

from pydantic import BaseModel

from antarest.core.utils.utils import assert_this
from antarest.study.storage.rawstudy.model.filesystem.config.model import (
    FileStudyTreeConfig,
)
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.model.command.common import (
    CommandOutput,
    CommandName,
)
from antarest.study.storage.variantstudy.model.command_context import (
    CommandContext,
)
from antarest.study.storage.variantstudy.model.model import CommandDTO

MATCH_SIGNATURE_SEPARATOR = "%"
logger = logging.getLogger(__name__)


class ICommand(ABC, BaseModel):
    command_name: CommandName
    version: int
    command_context: CommandContext

    @abstractmethod
    def _apply(self, study_data: FileStudy) -> CommandOutput:
        raise NotImplementedError()

    @abstractmethod
    def _apply_config(
        self, study_data: FileStudyTreeConfig
    ) -> Tuple[CommandOutput, Dict[str, Any]]:
        raise NotImplementedError()

    def apply_config(self, study_data: FileStudyTreeConfig) -> CommandOutput:
        output, _ = self._apply_config(study_data)
        return output

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
    def to_dto(self) -> CommandDTO:
        raise NotImplementedError()

    @abstractmethod
    def match_signature(self) -> str:
        raise NotImplementedError()

    @abstractmethod
    def match(self, other: "ICommand", equal: bool = False) -> bool:
        """
        Indicate if the other command is the same type and targets the same element.

        Args:
            other: other command to match against
            equal: indicate if the match must check for param equality

        Returns: True if the command match with the other else False
        """
        raise NotImplementedError()

    @abstractmethod
    def revert(
        self, history: List["ICommand"], base: FileStudy
    ) -> List["ICommand"]:
        """
        Returns the reverse command using history

        Args:
            history: list of previous commands
            base: base tree study

        Returns: a new command that reverts this one
        """
        raise NotImplementedError()

    def create_diff(self, other: "ICommand") -> List["ICommand"]:
        assert_this(self.match(other))
        return self._create_diff(other)

    @abstractmethod
    def _create_diff(self, other: "ICommand") -> List["ICommand"]:
        raise NotImplementedError()

    @abstractmethod
    def get_inner_matrices(self) -> List[str]:
        raise NotImplementedError()

    class Config:
        arbitrary_types_allowed = True
