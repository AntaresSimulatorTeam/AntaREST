from typing import Dict, Union, List

from antarest.study.storage.variantstudy.model.command.common import (
    CommandOutput,
    CommandName,
)
from antarest.study.storage.variantstudy.model.command.icommand import ICommand


class ReplaceMatrix(ICommand):
    target_element: str
    matrix: Union[List[List[float]], str]

    def __init__(self):
        super().__init__(command_name=CommandName.REPLACE_MATRIX)

    def apply(self) -> CommandOutput:
        raise NotImplementedError()
