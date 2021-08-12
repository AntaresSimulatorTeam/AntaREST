from typing import Dict, Union, List

from antarest.study.storage.variantstudy.model.command.common import (
    CommandOutput,
    CommandName,
)
from antarest.study.storage.variantstudy.model.command.icommand import ICommand


class UpdateConfig(ICommand):
    target: str
    data: Dict[str, str]

    def __init__(self):
        super().__init__(command_name=CommandName.UPDATE_CONFIG)

    def apply(self) -> CommandOutput:
        raise NotImplementedError()
