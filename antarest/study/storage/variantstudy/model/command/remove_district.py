from typing import Any, List, Optional

from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.model.model import CommandDTO
from antarest.study.storage.variantstudy.model.command.common import (
    CommandOutput,
    CommandName,
)
from antarest.study.storage.variantstudy.model.command.icommand import ICommand


class RemoveDistrict(ICommand):
    id: str

    def __init__(self, **data: Any) -> None:
        super().__init__(
            command_name=CommandName.REMOVE_DISTRICT, version=1, **data
        )

    def _apply(self, study_data: FileStudy) -> CommandOutput:
        del study_data.config.sets[self.id]
        study_data.tree.delete(["input", "areas", "sets", self.id])
        return CommandOutput(status=True, message=self.id)

    def to_dto(self) -> CommandDTO:
        return CommandDTO(
            action=CommandName.REMOVE_DISTRICT.value,
            args={
                "id": self.id,
            },
        )

    def match(self, other: ICommand, equal: bool = False) -> bool:
        if not isinstance(other, RemoveDistrict):
            return False
        return self.id == other.id

    def revert(self, history: List["ICommand"], base: FileStudy) -> Optional["ICommand"]:
        return None
