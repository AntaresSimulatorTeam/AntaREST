from typing import Dict, Any, Optional

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

    def _generate_new_thermal_areas_ini(
        self,
        file_study: FileStudy,
        unservedenergycost: Optional[int] = None,
        spilledenergycost: Optional[int] = None,
    ):
        new_areas = file_study.tree.get(url=["input", "thermal", "areas"])
        if unservedenergycost is not None:
            new_areas["unservedenergycost"][
                self.area_name
            ] = unservedenergycost
        if spilledenergycost is not None:
            new_areas["spilledenergycost"][self.area_name] = spilledenergycost

        return new_areas

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
                    self.area_name: {
                        "optimization": {},
                        "ui": {},
                    },  # TODO: initialize optimization and ui with default values
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
                    "prepro": {
                        self.area_name: {
                            "energy": command_context.generator_matrix_constants.get_hydro_energy(),
                            "prepro": {
                                "prepro": {"intermonthly-correlation": 0.5}
                            },
                        },
                    },
                    "series": {
                        self.area_name: {
                            "mod": command_context.generator_matrix_constants.get_hydro_series_mod(),
                            "ror": command_context.generator_matrix_constants.get_hydro_series_ror(),
                        },
                    },
                },
                "links": {self.area_name: {"properties": {}}},
                "load": {
                    "prepro": {
                        self.area_name: {
                            "conversion": command_context.generator_matrix_constants.get_load_prepro_conversion(),
                            "data": command_context.generator_matrix_constants.get_load_prepro_data(),
                            "k": command_context.generator_matrix_constants.get_load_prepro_k(),
                            "settings": {},
                            "translation": command_context.generator_matrix_constants.get_load_prepro_translation(),
                        }
                    },
                    "series": {
                        f"load_{self.area_name}": command_context.generator_matrix_constants.get_load_series_load_area_name()
                    },
                },
                "misc-gen": {
                    f"miscgen-{self.area_name}": command_context.generator_matrix_constants.get_misc_gen()
                },
                "reserves": {
                    self.area_name: command_context.generator_matrix_constants.get_reserves()
                },
                "solar": {
                    "prepro": {
                        self.area_name: {
                            "conversion": command_context.generator_matrix_constants.get_solar_prepro_conversion(),
                            "data": command_context.generator_matrix_constants.get_solar_prepro_data(),
                            "k": command_context.generator_matrix_constants.get_solar_prepro_k(),
                            "settings": {},
                            "translation": command_context.generator_matrix_constants.get_solar_prepro_translation(),
                        }
                    },
                    "series": {
                        f"solar_{self.area_name}": command_context.generator_matrix_constants.get_solar_series_load_area_name()
                    },
                },
                "thermal": {
                    "clusters": {self.area_name: {"list": {}}},
                    "areas": self._generate_new_thermal_areas_ini(  # TODO: add unservdenergycost and spilledenergycost
                        study_data
                    ),
                },
                "wind": {
                    "prepro": {
                        self.area_name: {
                            "conversion": command_context.generator_matrix_constants.get_wind_prepro_conversion(),
                            "data": command_context.generator_matrix_constants.get_wind_prepro_data(),
                            "k": command_context.generator_matrix_constants.get_wind_prepro_k(),
                            "settings": {},
                            "translation": command_context.generator_matrix_constants.get_wind_prepro_translation(),
                        }
                    },
                    "series": {
                        f"wind_{self.area_name}": command_context.generator_matrix_constants.get_wind_series_load_area_name()
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
                command_context.generator_matrix_constants.get_hydro_water_values()
            )

        study_data.tree.save(new_area_data)

        return CommandOutput(
            status=True, message=f"Area '{self.area_name}' created"
        )

    def revert(self, study_data: FileStudy) -> CommandOutput:
        raise NotImplementedError()
