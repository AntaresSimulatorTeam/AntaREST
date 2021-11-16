from typing import Any, List, Optional

from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.model.command.common import (
    CommandOutput,
    CommandName,
)
from antarest.study.storage.variantstudy.model.command.icommand import (
    ICommand,
    MATCH_SIGNATURE_SEPARATOR,
)
from antarest.study.storage.variantstudy.model.model import CommandDTO


class RemoveLink(ICommand):
    area1: str
    area2: str

    def __init__(self, **data: Any) -> None:
        super().__init__(
            command_name=CommandName.REMOVE_LINK, version=1, **data
        )

    def _apply(self, study_data: FileStudy) -> CommandOutput:
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

        area_from, area_to = sorted([self.area1, self.area2])

        if area_to not in study_data.config.areas[area_from].links:
            return CommandOutput(
                status=False,
                message=f"The link between {self.area1} and {self.area2} does not exist.",
            )

        study_data.tree.delete(["input", "links", area_from, area_to])
        study_data.tree.delete(
            ["input", "links", area_from, "properties", area_to]
        )
        return CommandOutput(
            status=True,
            message=f"Link between {self.area1} and {self.area2} removed",
        )

    def to_dto(self) -> CommandDTO:
        return CommandDTO(
            action=CommandName.REMOVE_LINK.value,
            args={
                "area1": self.area1,
                "area2": self.area2,
            },
        )

    def match_signature(self) -> str:
        return str(
            self.command_name.value
            + MATCH_SIGNATURE_SEPARATOR
            + self.area1
            + MATCH_SIGNATURE_SEPARATOR
            + self.area2
        )

    def match(self, other: ICommand, equal: bool = False) -> bool:
        if not isinstance(other, RemoveLink):
            return False
        return self.area1 == other.area1 and self.area2 == other.area2

    def revert(
        self, history: List["ICommand"], base: FileStudy
    ) -> List["ICommand"]:
        from antarest.study.storage.variantstudy.model.command.create_link import (
            CreateLink,
        )
        from antarest.study.storage.variantstudy.model.command.utils_extractor import (
            CommandExtraction,
        )

        for command in reversed(history):
            if (
                isinstance(command, CreateLink)
                and command.area1 == self.area1
                and command.area2 == self.area2
            ):
                return [command]
        area_from, area_to = sorted([self.area1, self.area2])
        return (
            self.command_context.command_extractor
            or CommandExtraction(self.command_context.matrix_service)
        ).extract_link(base, area_from, area_to)

    def _create_diff(self, other: "ICommand") -> List["ICommand"]:
        return []

    def get_inner_matrices(self) -> List[str]:
        return []
