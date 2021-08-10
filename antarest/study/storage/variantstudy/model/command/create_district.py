from typing import Dict

from antarest.study.storage.variantstudy.model.command.common import (
    CommandOutput,
)
from antarest.study.storage.variantstudy.model.command.icommand import ICommand


class CreateDistrict(ICommand):
    id: str
    metadata: Dict[str, str]

    def __init__(self):
        super().__init__(command_name="create_district")

    def apply(self) -> CommandOutput:
        raise NotImplementedError()
