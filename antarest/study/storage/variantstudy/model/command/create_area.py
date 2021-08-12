from typing import Dict

from antarest.study.storage.variantstudy.model.command.common import (
    CommandOutput,
    CommandName,
)
from antarest.study.storage.variantstudy.model.command.icommand import ICommand


class CreateArea(ICommand):
    name: str
    metadata: Dict[str, str]

    def __init__(self):
        super().__init__(command_name=CommandName.CREATE_AREA)

    def apply(self) -> CommandOutput:
        raise NotImplementedError()
