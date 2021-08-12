from typing import Dict, Union, List

from antarest.study.storage.variantstudy.model.command.common import (
    CommandOutput,
    CommandName,
)
from antarest.study.storage.variantstudy.model.command.icommand import ICommand


class UpdateCluster(ICommand):
    id: str
    name: str
    type: str
    parameters: Dict[str, str]
    prepro: Union[List[List[float]], str]
    modulation: Union[List[List[float]], str]

    def __init__(self):
        super().__init__(command_name=CommandName.UPDATE_CLUSTER)

    def apply(self) -> CommandOutput:
        raise NotImplementedError()
