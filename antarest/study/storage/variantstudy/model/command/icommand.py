import logging
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Dict, List, Tuple

from pydantic import BaseModel

from antarest.core.utils.utils import assert_this
from antarest.study.storage.rawstudy.model.filesystem.config.model import FileStudyTreeConfig
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.model.command.common import CommandName, CommandOutput
from antarest.study.storage.variantstudy.model.command_context import CommandContext
from antarest.study.storage.variantstudy.model.model import CommandDTO

if TYPE_CHECKING:  # False at runtime, for mypy
    from antarest.study.storage.variantstudy.business.command_extractor import CommandExtractor

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
            message = (
                f"Unexpected exception occurred when trying"
                f" to apply command {self.command_name}: {e}"
            )
            return CommandOutput(status=False, message=message)

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

    def create_diff(self, other: "ICommand") -> List["ICommand"]:
        assert_this(self.match(other))
        return self._create_diff(other)

    @abstractmethod
    def _create_diff(self, other: "ICommand") -> List["ICommand"]:
        raise NotImplementedError()

    @abstractmethod
    def get_inner_matrices(self) -> List[str]:
        raise NotImplementedError()

    def get_command_extractor(self) -> "CommandExtractor":
        from antarest.study.storage.variantstudy.business.command_extractor import CommandExtractor

        return CommandExtractor(
            self.command_context.matrix_service,
            self.command_context.patch_service,
        )

    class Config:
        arbitrary_types_allowed = True
