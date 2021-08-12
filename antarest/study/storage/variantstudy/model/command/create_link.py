from typing import Dict, List, Union

from antarest.study.storage.variantstudy.model.command.common import (
    CommandOutput,
    CommandName,
)
from antarest.study.storage.variantstudy.model.command.icommand import ICommand


class CreateLink(ICommand):
    name: str
    parameters: Dict[str, str]
    series: Union[List[List[float]], str]

    def __init__(self):
        super().__init__(command_name=CommandName.CREATE_LINK)

    def apply(self) -> CommandOutput:
        raise NotImplementedError()
