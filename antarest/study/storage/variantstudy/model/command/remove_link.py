from antarest.study.storage.variantstudy.model.command.common import (
    CommandOutput,
)
from antarest.study.storage.variantstudy.model.command.icommand import ICommand


class RemoveLink(ICommand):
    id: str

    def __init__(self):
        super().__init__(command_name="remove_link")

    def apply(self) -> CommandOutput:
        raise NotImplementedError()
