from typing import Any, Dict, List, Tuple

from antarest.study.storage.rawstudy.model.filesystem.config.model import FileStudyTreeConfig
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.model.command.common import CommandName, CommandOutput
from antarest.study.storage.variantstudy.model.command.icommand import MATCH_SIGNATURE_SEPARATOR, ICommand
from antarest.study.storage.variantstudy.model.model import CommandDTO


class RemoveLink(ICommand):
    """
    Command used to remove a link.
    """

    # Overloaded metadata
    # ===================

    command_name = CommandName.REMOVE_LINK
    version: int = 1

    # Command parameters
    # ==================

    # Properties of the `REMOVE_LINK` command:
    area1: str
    area2: str

    def _apply_config(self, study_data: FileStudyTreeConfig) -> Tuple[CommandOutput, Dict[str, Any]]:
        result = self._check_link_exists(study_data)
        if result[0].status:
            area_from, area_to = sorted([self.area1, self.area2])
            del study_data.areas[area_from].links[area_to]
        return result

    def _check_link_exists(self, study_data: FileStudyTreeConfig) -> Tuple[CommandOutput, Dict[str, Any]]:
        if self.area1 not in study_data.areas:
            return (
                CommandOutput(
                    status=False,
                    message=f"The area '{self.area1}' does not exist.",
                ),
                dict(),
            )
        if self.area2 not in study_data.areas:
            return (
                CommandOutput(
                    status=False,
                    message=f"The area '{self.area2}' does not exist.",
                ),
                dict(),
            )

        area_from, area_to = sorted([self.area1, self.area2])

        if area_to not in study_data.areas[area_from].links:
            return (
                CommandOutput(
                    status=False,
                    message=f"The link between {self.area1} and {self.area2} does not exist.",
                ),
                dict(),
            )
        return (
            CommandOutput(
                status=True,
                message=f"Link between {self.area1} and {self.area2} removed",
            ),
            {"area_from": area_from, "area_to": area_to},
        )

    def _apply(self, study_data: FileStudy) -> CommandOutput:
        output, data = self._check_link_exists(study_data.config)
        if not output.status:
            return output
        area_from = data["area_from"]
        area_to = data["area_to"]
        if study_data.config.version < 820:
            study_data.tree.delete(["input", "links", area_from, area_to])
        else:
            study_data.tree.delete(["input", "links", area_from, f"{area_to}_parameters"])
            study_data.tree.delete(
                [
                    "input",
                    "links",
                    area_from,
                    "capacities",
                    f"{area_to}_direct",
                ]
            )
            study_data.tree.delete(
                [
                    "input",
                    "links",
                    area_from,
                    "capacities",
                    f"{area_to}_indirect",
                ]
            )
        study_data.tree.delete(["input", "links", area_from, "properties", area_to])
        del study_data.config.areas[area_from].links[area_to]
        return output

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
            self.command_name.value + MATCH_SIGNATURE_SEPARATOR + self.area1 + MATCH_SIGNATURE_SEPARATOR + self.area2
        )

    def match(self, other: ICommand, equal: bool = False) -> bool:
        if not isinstance(other, RemoveLink):
            return False
        return self.area1 == other.area1 and self.area2 == other.area2

    def _create_diff(self, other: "ICommand") -> List["ICommand"]:
        return []

    def get_inner_matrices(self) -> List[str]:
        return []
