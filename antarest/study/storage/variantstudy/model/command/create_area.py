from typing import Dict, Any, Optional

from pydantic import validator

from antarest.core.custom_types import JSON
from antarest.study.storage.rawstudy.model.filesystem.config.model import Area
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.business.default_values import (
    NodalOptimization,
    FilteringOptions,
)
from antarest.study.storage.variantstudy.model.command.common import (
    CommandOutput,
    CommandName,
)
from antarest.study.storage.variantstudy.model.command.icommand import ICommand


class CreateArea(ICommand):
    area_name: str
    metadata: Dict[str, str]  # TODO: use metadata

    def __init__(self, **data: Any) -> None:
        super().__init__(
            command_name=CommandName.CREATE_AREA,
            version=1,
            **data,
        )

    def _generate_new_thermal_areas_ini(
        self,
        file_study: FileStudy,
        unservedenergycost: Optional[int] = None,
        spilledenergycost: Optional[int] = None,
    ) -> JSON:
        new_areas: JSON = file_study.tree.get(
            url=["input", "thermal", "areas"]
        )
        if unservedenergycost is not None:
            new_areas["unserverdenergycost"][
                self.area_name
            ] = unservedenergycost
        if spilledenergycost is not None:
            new_areas["spilledenergycost"][self.area_name] = spilledenergycost

        return new_areas

    def apply(self, study_data: FileStudy) -> CommandOutput:
        if self.command_context.generator_matrix_constants is None:
            raise ValueError()

        if self.area_name in study_data.config.areas.keys():
            return CommandOutput(
                status=False,
                message=f"Area '{self.area_name}' already exists and could not be created",
            )

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
                        "optimization": {
                            "nodal optimization": {
                                "non-dispatchable-power": NodalOptimization.NON_DISPATCHABLE_POWER.value,
                                "dispatchable-hydro-power": NodalOptimization.DISPATCHABLE_HYDRO_POWER.value,
                                "other-dispatchable-power": NodalOptimization.OTHER_DISPATCHABLE_POWER.value,
                                "spread-unsupplied-energy-cost": NodalOptimization.SPREAD_UNSUPPLIED_ENERGY_COST.value,
                                "spread-spilled-energy-cost": NodalOptimization.SPREAD_SPILLED_ENERGY_COST.value,
                            },
                            "filtering": {
                                "filter-synthesis": FilteringOptions.FILTER_SYNTHESIS.value,
                                "filter-year-by-year": FilteringOptions.FILTER_YEAR_BY_YEAR.value,
                            },
                        },
                        "ui": {
                            "ui": {
                                "x": 0,
                                "y": 0,
                                "color_r": 230,
                                "color_g": 108,
                                "color_b": 44,
                                "layers": 0,
                            },
                            "layerX": {"O": 0},
                            "layerY": {"O": 0},
                            "layerColor": {"O": "230 , 108 , 44"},
                        },
                    },
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
                            f"maxpower_{self.area_name}": self.command_context.generator_matrix_constants.get_hydro_max_power(
                                version=version
                            ),
                            f"reservoir_{self.area_name}": self.command_context.generator_matrix_constants.get_hydro_reservoir(
                                version=version
                            ),
                        }
                    },
                    "prepro": {
                        self.area_name: {
                            "energy": self.command_context.generator_matrix_constants.get_null_matrix(),
                            "prepro": {
                                "prepro": {"intermonthly-correlation": 0.5}
                            },
                        },
                    },
                    "series": {
                        self.area_name: {
                            "mod": self.command_context.generator_matrix_constants.get_null_matrix(),
                            "ror": self.command_context.generator_matrix_constants.get_null_matrix(),
                        },
                    },
                },
                "links": {self.area_name: {"properties": {}}},
                "load": {
                    "prepro": {
                        self.area_name: {
                            "conversion": self.command_context.generator_matrix_constants.get_prepro_conversion(),
                            "data": self.command_context.generator_matrix_constants.get_prepro_data(),
                            "k": self.command_context.generator_matrix_constants.get_null_matrix(),
                            "settings": {},
                            "translation": self.command_context.generator_matrix_constants.get_null_matrix(),
                        }
                    },
                    "series": {
                        f"load_{self.area_name}": self.command_context.generator_matrix_constants.get_null_matrix(),
                    },
                },
                "misc-gen": {
                    f"miscgen-{self.area_name}": self.command_context.generator_matrix_constants.get_null_matrix()
                },
                "reserves": {
                    self.area_name: self.command_context.generator_matrix_constants.get_null_matrix()
                },
                "solar": {
                    "prepro": {
                        self.area_name: {
                            "conversion": self.command_context.generator_matrix_constants.get_prepro_conversion(),
                            "data": self.command_context.generator_matrix_constants.get_prepro_data(),
                            "k": self.command_context.generator_matrix_constants.get_null_matrix(),
                            "settings": {},
                            "translation": self.command_context.generator_matrix_constants.get_null_matrix(),
                        }
                    },
                    "series": {
                        f"solar_{self.area_name}": self.command_context.generator_matrix_constants.get_null_matrix(),
                    },
                },
                "thermal": {
                    "clusters": {self.area_name: {"list": {}}},
                    "areas": self._generate_new_thermal_areas_ini(
                        study_data,
                        unservedenergycost=NodalOptimization.UNSERVERDDENERGYCOST.value,
                        spilledenergycost=NodalOptimization.SPILLEDENERGYCOST.value,
                    ),
                },
                "wind": {
                    "prepro": {
                        self.area_name: {
                            "conversion": self.command_context.generator_matrix_constants.get_prepro_conversion(),
                            "data": self.command_context.generator_matrix_constants.get_prepro_data(),
                            "k": self.command_context.generator_matrix_constants.get_null_matrix(),
                            "settings": {},
                            "translation": self.command_context.generator_matrix_constants.get_null_matrix(),
                        }
                    },
                    "series": {
                        f"wind_{self.area_name}": self.command_context.generator_matrix_constants.get_null_matrix()
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
                self.command_context.generator_matrix_constants.get_hydro_credit_modulations()
            )
            new_area_data["input"]["hydro"]["common"]["capacity"][
                f"inflowPattern_{self.area_name}"
            ] = (
                self.command_context.generator_matrix_constants.get_hydro_inflow_pattern()
            )
            new_area_data["input"]["hydro"]["common"]["capacity"][
                f"waterValues_{self.area_name}"
            ] = (
                self.command_context.generator_matrix_constants.get_null_matrix()
            )

        study_data.tree.save(new_area_data)

        return CommandOutput(
            status=True, message=f"Area '{self.area_name}' created"
        )

    def revert(self, study_data: FileStudy) -> CommandOutput:
        raise NotImplementedError()
