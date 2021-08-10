from typing import Dict, List

from antarest.study.storage.variantstudy.model.command.common import (
    CommandOutput,
)
from antarest.study.storage.variantstudy.model.command.icommand import ICommand


class UpdateDistrict(ICommand):
    id: str
    name: str
    metadata: Dict[str, str]
    set: List[str]

    def __init__(self):
        super().__init__(command_name="update_district")

    def apply(self) -> CommandOutput:
        raise NotImplementedError()
