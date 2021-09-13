from typing import Any

from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
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

    def apply(self, study_data: FileStudy) -> CommandOutput:
        del study_data.config.sets[self.id]
        study_data.tree.delete(["input", "areas", "sets", self.id])
        return CommandOutput(status=True, message=self.id)

    def revert(self, study_data: FileStudy) -> CommandOutput:
        raise NotImplementedError()
