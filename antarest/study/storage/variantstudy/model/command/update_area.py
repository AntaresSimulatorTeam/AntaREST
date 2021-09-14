from typing import Dict, Any

from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.model.model import CommandDTO
from antarest.study.storage.variantstudy.model.command.common import (
    CommandOutput,
    CommandName,
)
from antarest.study.storage.variantstudy.model.command.icommand import ICommand


class UpdateArea(ICommand):
    id: str
    name: str
    metadata: Dict[str, str]

    def __init__(self, **data: Any) -> None:
        super().__init__(
            command_name=CommandName.UPDATE_AREA, version=1, **data
        )

    def _apply(self, study_data: FileStudy) -> CommandOutput:
        raise NotImplementedError()

    def to_dto(self) -> CommandDTO:
        return CommandDTO(
            action=CommandName.UPDATE_AREA.value,
            args={"id": self.id, "name": self.name, "metadata": self.metadata},
        )
