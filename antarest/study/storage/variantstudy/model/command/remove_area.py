from typing import Any

from antarest.core.custom_types import JSON
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.model.command.common import (
    CommandOutput,
    CommandName,
)
from antarest.study.storage.variantstudy.model.command.icommand import ICommand


class RemoveArea(ICommand):
    id: str

    def __init__(self, **data: Any) -> None:
        super().__init__(
            command_name=CommandName.REMOVE_AREA, version=1, **data
        )

    def apply(self, study_data: FileStudy) -> CommandOutput:

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
        for area_name in study_data.config.areas.keys():
            study_data.tree.delete(["input", "links", area_name, self.id])

        new_area_data: JSON = {
            "input": {
                "areas": {
                    "list": study_data.config.areas.keys(),
                }
            }
        }
        study_data.tree.save(new_area_data)

        return CommandOutput(status=True, message=f"Area '{self.id}' deleted")

    def revert(self, study_data: FileStudy) -> CommandOutput:
        raise NotImplementedError()
