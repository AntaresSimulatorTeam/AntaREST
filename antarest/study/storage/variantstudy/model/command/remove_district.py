import logging
from typing import Any, List, Optional, Tuple, Dict

from antarest.study.storage.rawstudy.model.filesystem.config.model import (
    transform_name_to_id,
    FileStudyTreeConfig,
)
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.rawstudy.model.filesystem.folder_node import (
    ChildNotFoundError,
)
from antarest.study.storage.variantstudy.model.command.common import (
    CommandOutput,
    CommandName,
)
from antarest.study.storage.variantstudy.model.command.icommand import (
    ICommand,
    MATCH_SIGNATURE_SEPARATOR,
)
from antarest.study.storage.variantstudy.model.model import CommandDTO


class RemoveDistrict(ICommand):
    id: str

    def __init__(self, **data: Any) -> None:
        super().__init__(
            command_name=CommandName.REMOVE_DISTRICT, version=1, **data
        )

    def _apply_config(
        self, study_data: FileStudyTreeConfig
    ) -> Tuple[CommandOutput, Dict[str, Any]]:
        del study_data.sets[self.id]
        return CommandOutput(status=True, message=self.id), dict()

    def _apply(self, study_data: FileStudy) -> CommandOutput:
        output, _ = self._apply_config(study_data.config)
        study_data.tree.delete(["input", "areas", "sets", self.id])
        return output

    def to_dto(self) -> CommandDTO:
        return CommandDTO(
            action=CommandName.REMOVE_DISTRICT.value,
            args={
                "id": self.id,
            },
        )

    def match_signature(self) -> str:
        return str(
            self.command_name.value + MATCH_SIGNATURE_SEPARATOR + self.id
        )

    def match(self, other: ICommand, equal: bool = False) -> bool:
        if not isinstance(other, RemoveDistrict):
            return False
        return self.id == other.id

    def revert(
        self, history: List["ICommand"], base: FileStudy
    ) -> List["ICommand"]:
        from antarest.study.storage.variantstudy.model.command.create_district import (
            CreateDistrict,
        )
        from antarest.study.storage.variantstudy.model.command.utils_extractor import (
            CommandExtraction,
        )

        for command in reversed(history):
            if (
                isinstance(command, CreateDistrict)
                and transform_name_to_id(command.name) == self.id
            ):
                return [command]
        try:
            return (
                self.command_context.command_extractor
                or CommandExtraction(self.command_context.matrix_service)
            ).extract_district(base, self.id)
        except Exception as e:
            logging.getLogger(__name__).warning(
                f"Failed to extract revert command for remove_district {self.id}",
                exc_info=e,
            )
            return []

    def _create_diff(self, other: "ICommand") -> List["ICommand"]:
        return []

    def get_inner_matrices(self) -> List[str]:
        return []
