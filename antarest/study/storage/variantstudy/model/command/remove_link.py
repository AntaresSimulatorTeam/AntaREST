from typing import Any

from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.model.command.common import (
    CommandOutput,
    CommandName,
)
from antarest.study.storage.variantstudy.model.command.icommand import ICommand


class RemoveLink(ICommand):
    area1: str
    area2: str

    def __init__(self, **data: Any) -> None:
        super().__init__(
            command_name=CommandName.REMOVE_LINK, version=1, **data
        )

    def apply(self, study_data: FileStudy) -> CommandOutput:
        if self.area1 not in study_data.config.areas:
            return CommandOutput(
                status=False,
                message=f"The area '{self.area1}' does not exist.",
            )
        if self.area2 not in study_data.config.areas:
            return CommandOutput(
                status=False,
                message=f"The area '{self.area2}' does not exist.",
            )

        if self.area2 not in study_data.config.areas[self.area1].links:
            return CommandOutput(
                status=False,
                message=f"The link between {self.area1} and {self.area2} does not exist.",
            )
        if self.area1 not in study_data.config.areas[self.area2].links:
            return CommandOutput(
                status=False,
                message=f"The link between {self.area1} and {self.area2} does not exist.",
            )

        area_from, area_to = sorted([self.area1, self.area2])
        study_data.tree.delete(["input", "links", area_from, area_to])
        study_data.tree.delete(
            ["input", "links", area_from, "properties", area_to]
        )
        return CommandOutput(
            status=True,
            message=f"Link between {self.area1} and {self.area2} removed",
        )

    def revert(self, study_data: FileStudy) -> CommandOutput:
        raise NotImplementedError()
