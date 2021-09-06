from typing import Dict, List, Union, Any

from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.model.command.common import (
    CommandOutput,
    CommandName,
)
from antarest.study.storage.variantstudy.model.command.icommand import ICommand


class UpdateLink(ICommand):
    id: str
    name: str
    parameters: Dict[str, str]
    series: Union[List[List[float]], str]

    def __init__(self, **data: Any) -> None:
        super().__init__(
            command_name=CommandName.UPDATE_LINK, version=1, **data
        )

    def apply(self, study_data: FileStudy) -> CommandOutput:
        raise NotImplementedError()

    def revert(self, study_data: FileStudy) -> CommandOutput:
        raise NotImplementedError()
