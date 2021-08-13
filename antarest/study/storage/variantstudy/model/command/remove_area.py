from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.model.command.common import (
    CommandOutput,
    CommandName,
)
from antarest.study.storage.variantstudy.model.command.icommand import ICommand


class RemoveArea(ICommand):
    id: str

    def __init__(self):
        super().__init__(command_name=CommandName.REMOVE_AREA, version=1)

    def apply(self, study_data: FileStudy) -> CommandOutput:
        raise NotImplementedError()

    def revert(self, study_data: FileStudy) -> CommandOutput:
        raise NotImplementedError()
