from typing import Any, List, Optional

from antarest.core.custom_types import JSON
from antarest.study.model import PatchLeafDict
from antarest.study.storage.rawstudy.model.filesystem.config.model import (
    transform_name_to_id,
)
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.model.model import CommandDTO
from antarest.study.storage.variantstudy.model.command.common import (
    CommandOutput,
    CommandName,
)
from antarest.study.storage.variantstudy.model.command.icommand import (
    ICommand,
    MATCH_SIGNATURE_SEPARATOR,
)


class RemoveArea(ICommand):
    id: str

    def __init__(self, **data: Any) -> None:
        super().__init__(
            command_name=CommandName.REMOVE_AREA, version=1, **data
        )

    def _apply(self, study_data: FileStudy) -> CommandOutput:

        study_data.tree.delete(["input", "areas", self.id])

        study_data.tree.delete(["input", "hydro", "allocation", self.id])
        study_data.tree.delete(
            ["input", "hydro", "common", "capacity", f"maxpower_{self.id}"]
        )
        study_data.tree.delete(
            ["input", "hydro", "common", "capacity", f"reservoir_{self.id}"]
        )
        study_data.tree.delete(["input", "hydro", "prepro", self.id])
        study_data.tree.delete(["input", "hydro", "series", self.id])
        study_data.tree.delete(
            ["input", "hydro", "hydro", "inter-daily-breakdown", self.id]
        )
        study_data.tree.delete(
            ["input", "hydro", "hydro", "intra-daily-modulation", self.id]
        )
        study_data.tree.delete(
            ["input", "hydro", "hydro", "inter-monthly-breakdown", self.id]
        )
        study_data.tree.delete(["input", "load", "prepro", self.id])
        study_data.tree.delete(["input", "load", "series", f"load_{self.id}"])
        study_data.tree.delete(["input", "misc-gen", f"miscgen-{self.id}"])
        study_data.tree.delete(["input", "reserves", self.id])
        study_data.tree.delete(["input", "solar", "prepro", self.id])
        study_data.tree.delete(
            ["input", "solar", "series", f"solar_{self.id}"]
        )
        study_data.tree.delete(["input", "thermal", "clusters", self.id])
        study_data.tree.delete(
            ["input", "thermal", "areas", "unserverdenergycost", self.id]
        )
        study_data.tree.delete(
            ["input", "thermal", "areas", "spilledenergycost", self.id]
        )
        study_data.tree.delete(["input", "wind", "prepro", self.id])
        study_data.tree.delete(["input", "wind", "series", f"wind_{self.id}"])
        study_data.tree.delete(["input", "links", self.id])

        if study_data.config.version > 650:
            study_data.tree.delete(
                [
                    "input",
                    "hydro",
                    "hydro",
                    "initialize reservoir date",
                    self.id,
                ]
            )
            study_data.tree.delete(
                [
                    "input",
                    "hydro",
                    "hydro",
                    "leeway low",
                    self.id,
                ]
            )
            study_data.tree.delete(
                [
                    "input",
                    "hydro",
                    "hydro",
                    "leeway up",
                    self.id,
                ]
            )
            study_data.tree.delete(
                [
                    "input",
                    "hydro",
                    "hydro",
                    "pumping efficiency",
                    self.id,
                ]
            )
            study_data.tree.delete(
                [
                    "input",
                    "hydro",
                    "common",
                    "capacity",
                    f"creditmodulations_{self.id}",
                ]
            )
            study_data.tree.delete(
                [
                    "input",
                    "hydro",
                    "common",
                    "capacity",
                    f"inflowPattern_{self.id}",
                ]
            )
            study_data.tree.delete(
                [
                    "input",
                    "hydro",
                    "common",
                    "capacity",
                    f"waterValues_{self.id}",
                ]
            )

        del study_data.config.areas[self.id]
        for area_name, area in study_data.config.areas.items():
            for link in area.links.keys():
                if link == self.id:
                    study_data.tree.delete(
                        ["input", "links", area_name, self.id]
                    )

        new_area_data: JSON = {
            "input": {
                "areas": {
                    "list": [
                        area.name for area in study_data.config.areas.values()
                    ],
                }
            }
        }
        study_data.tree.save(new_area_data)

        # todo remove bindinconstraint using this area ?
        # todo remove area from districts
        return CommandOutput(status=True, message=f"Area '{self.id}' deleted")

    def to_dto(self) -> CommandDTO:
        return CommandDTO(
            action=CommandName.REMOVE_AREA.value,
            args={
                "id": self.id,
            },
        )

    def match_signature(self) -> str:
        return str(
            self.command_name.value + MATCH_SIGNATURE_SEPARATOR + self.id
        )

    def match(self, other: ICommand, equal: bool = False) -> bool:
        if not isinstance(other, RemoveArea):
            return False
        return self.id == other.id

    def revert(
        self, history: List["ICommand"], base: Optional[FileStudy] = None
    ) -> List["ICommand"]:
        from antarest.study.storage.variantstudy.model.command.create_area import (
            CreateArea,
        )
        from antarest.study.storage.variantstudy.model.command.utils_extractor import (
            CommandExtraction,
        )

        for command in reversed(history):
            if (
                isinstance(command, CreateArea)
                and transform_name_to_id(command.area_name) == self.id
            ):
                # todo revert binding constraints that has the area in constraint and also search in base for one
                return [command]
        if base is not None:

            area_commands, links_commands = (
                self.command_context.command_extractor
                or CommandExtraction(self.command_context.matrix_service)
            ).extract_area(base, self.id)
            return area_commands + links_commands
        # todo revert binding constraints that has the area in constraint
        return []

    def _create_diff(self, other: "ICommand") -> List["ICommand"]:
        return []

    def get_inner_matrices(self) -> List[str]:
        return []
