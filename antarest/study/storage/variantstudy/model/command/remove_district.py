from antarest.study.storage.variantstudy.model.command.common import (
    CommandOutput,
    CommandName,
)
from antarest.study.storage.variantstudy.model.command.icommand import ICommand


class RemoveDistrict(ICommand):
    id: str

    def __init__(self):
        super().__init__(command_name=CommandName.REMOVE_DISTRICT)

    def apply(self) -> CommandOutput:
        raise NotImplementedError()
