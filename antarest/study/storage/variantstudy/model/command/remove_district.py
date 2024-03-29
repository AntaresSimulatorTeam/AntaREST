from typing import Any, Dict, List, Tuple

from antarest.study.storage.rawstudy.model.filesystem.config.model import FileStudyTreeConfig
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.model.command.common import CommandName, CommandOutput
from antarest.study.storage.variantstudy.model.command.icommand import MATCH_SIGNATURE_SEPARATOR, ICommand
from antarest.study.storage.variantstudy.model.model import CommandDTO


class RemoveDistrict(ICommand):
    """
    Command used to remove a district from the study.
    """

    # Overloaded metadata
    # ===================

    command_name = CommandName.REMOVE_DISTRICT
    version = 1

    # Command parameters
    # ==================

    id: str

    def _apply_config(self, study_data: FileStudyTreeConfig) -> Tuple[CommandOutput, Dict[str, Any]]:
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
        return str(self.command_name.value + MATCH_SIGNATURE_SEPARATOR + self.id)

    def match(self, other: ICommand, equal: bool = False) -> bool:
        if not isinstance(other, RemoveDistrict):
            return False
        return self.id == other.id

    def _create_diff(self, other: "ICommand") -> List["ICommand"]:
        return []

    def get_inner_matrices(self) -> List[str]:
        return []
