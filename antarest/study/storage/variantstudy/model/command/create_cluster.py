from typing import Dict, Union, List

from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.model.command.common import (
    CommandOutput,
    CommandName,
)
from antarest.study.storage.variantstudy.model.command.icommand import ICommand


class CreateCluster(ICommand):
    name: str
    type: str
    parameters: Dict[str, str]
    prepro: Union[List[List[float]], str]
    modulation: Union[List[List[float]], str]

    def __init__(self):
        super().__init__(command_name=CommandName.CREATE_CLUSTER, version=1)

    def apply(self, study_data: FileStudy) -> CommandOutput:
        raise NotImplementedError()

    def revert(self, study_data: FileStudy) -> CommandOutput:
        raise NotImplementedError()
