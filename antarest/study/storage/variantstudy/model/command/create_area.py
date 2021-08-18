from typing import Dict, Any

from antarest.core.custom_types import JSON
from antarest.study.storage.rawstudy.model.filesystem.config.model import Area
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.model.command.common import (
    CommandOutput,
    CommandName,
)
from antarest.study.storage.variantstudy.model.command.icommand import ICommand
from antarest.study.storage.variantstudy.model.command_context import (
    CommandContext,
)


class CreateArea(ICommand):
    area_name: str
    metadata: Dict[str, str]

    def __init__(self, **data: Any) -> None:
        super().__init__(
            command_name=CommandName.CREATE_AREA, version=1, **data
        )

    def apply(
        self, study_data: FileStudy, command_context: CommandContext
    ) -> CommandOutput:
        version = study_data.config.version

        study_data.config.areas[self.area_name] = Area(
            links={},
            thermals=[],
            renewables=[],
            filters_synthesis=[],
            filters_year=[],
        )

        new_area_data: JSON = {
            "input": {
                "areas": {
                    "list": study_data.config.areas.keys(),
                    self.area_name: {"optimization": {}, "ui": {}},
                },
                "hydro": {
                    "hydro": {
                        "inter-daily-breakdown": {self.area_name: 1},
                        "intra-daily-modulation": {self.area_name: 24},
                        "inter-monthly-breakdown": {self.area_name: 1},
                    },
                    "allocation": {
                        self.area_name: {"[allocation]": {self.area_name: 1}}
                    },
                    "common": {
                        "capacity": {
                            f"maxpower_{self.area_name}": command_context.generator_matrix_constants.get_hydro_max_power(
                                version=version
                            ),
                            f"reservoir_{self.area_name}": command_context.generator_matrix_constants.get_hydro_reservoir(
                                version=version
                            ),
                        }
                    },
                },
            }
        }

        if version > 650:
            new_area_data["input"]["hydro"]["hydro"][
                "initialize reservoir date"
            ] = {self.area_name: 0}
            new_area_data["input"]["hydro"]["hydro"]["leeway low"] = {
                self.area_name: 1
            }
            new_area_data["input"]["hydro"]["hydro"]["leeway up"] = {
                self.area_name: 1
            }
            new_area_data["input"]["hydro"]["hydro"]["pumping efficiency"] = {
                self.area_name: 1
            }
            new_area_data["input"]["hydro"]["common"]["capacity"][
                f"creditmodulations_{self.area_name}"
            ] = (
                command_context.generator_matrix_constants.get_hydro_credit_modulations()
            )
            new_area_data["input"]["hydro"]["common"]["capacity"][
                f"inflowPattern_{self.area_name}"
            ] = (
                command_context.generator_matrix_constants.get_hydro_inflow_pattern()
            )
            new_area_data["input"]["hydro"]["common"]["capacity"][
                f"waterValues_{self.area_name}"
            ] = (
                command_context.generator_matrix_constants.get_hydro_credit_water_values()
            )

        study_data.tree.save(new_area_data)

        pass

    def revert(self, study_data: FileStudy) -> CommandOutput:
        raise NotImplementedError()
