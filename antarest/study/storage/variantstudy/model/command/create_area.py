from typing import Dict, Any, Optional

from pydantic import validator

from antarest.core.custom_types import JSON
from antarest.study.storage.rawstudy.model.filesystem.config.model import (
    Area,
    transform_name_to_id,
)
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
from antarest.study.storage.variantstudy.model.command.utils import (
    get_or_create_section,
)


class CreateArea(ICommand):
    area_name: str
    metadata: Dict[str, str]  # TODO: use metadata

    def __init__(self, **data: Any) -> None:
        super().__init__(
            command_name=CommandName.CREATE_AREA,
            version=1,
            **data,
        )

    @validator("area_name")
    def validate_area_name(cls, val: str) -> str:
        valid_name = transform_name_to_id(val, lower=False)
        if valid_name != val:
            raise ValueError(
                "Area name must only contains [a-zA-Z0-9],&,-,_,(,) characters"
            )
        return val

    def _generate_new_thermal_areas_ini(
        self,
        file_study: FileStudy,
        area_id: str,
        unservedenergycost: Optional[float] = None,
        spilledenergycost: Optional[float] = None,
    ) -> JSON:
        new_areas: JSON = file_study.tree.get(
            url=["input", "thermal", "areas"]
        )
        if unservedenergycost is not None:
            new_areas["unserverdenergycost"][area_id] = unservedenergycost
        if spilledenergycost is not None:
            new_areas["spilledenergycost"][area_id] = spilledenergycost

        return new_areas

    def apply(self, study_data: FileStudy) -> CommandOutput:
        if self.command_context.generator_matrix_constants is None:
            raise ValueError()

        area_id = transform_name_to_id(self.area_name)

        if area_id in study_data.config.areas.keys():
            return CommandOutput(
                status=False,
                message=f"Area '{self.area_name}' already exists and could not be created",
            )

        version = study_data.config.version

        study_data.config.areas[area_id] = Area(
            name=self.area_name,
            links={},
            thermals=[],
            renewables=[],
            filters_synthesis=[],
            filters_year=[],
        )

        hydro_config = study_data.tree.get(["input", "hydro", "hydro"])
        get_or_create_section(hydro_config, "inter-daily-breakdown")[
            area_id
        ] = 1
        get_or_create_section(hydro_config, "intra-daily-modulation")[
            area_id
        ] = 24
        get_or_create_section(hydro_config, "inter-monthly-breakdown")[
            area_id
        ] = 1

        new_area_data: JSON = {
            "input": {
                "areas": {
                    "list": [
                        area.name for area in study_data.config.areas.values()
                    ],
                    area_id: {
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
                        # this will ini file must be edited (using hydro_config)
                    },
                    "allocation": {area_id: {"[allocation]": {area_id: 1}}},
                    "common": {
                        "capacity": {
                            f"maxpower_{area_id}": self.command_context.generator_matrix_constants.get_hydro_max_power(
                                version=version
                            ),
                            f"reservoir_{area_id}": self.command_context.generator_matrix_constants.get_hydro_reservoir(
                                version=version
                            ),
                        }
                    },
                    "prepro": {
                        area_id: {
                            "energy": self.command_context.generator_matrix_constants.get_null_matrix(),
                            "prepro": {
                                "prepro": {"intermonthly-correlation": 0.5}
                            },
                        },
                    },
                    "series": {
                        area_id: {
                            "mod": self.command_context.generator_matrix_constants.get_null_matrix(),
                            "ror": self.command_context.generator_matrix_constants.get_null_matrix(),
                        },
                    },
                },
                "links": {area_id: {"properties": {}}},
                "load": {
                    "prepro": {
                        area_id: {
                            "conversion": self.command_context.generator_matrix_constants.get_prepro_conversion(),
                            "data": self.command_context.generator_matrix_constants.get_prepro_data(),
                            "k": self.command_context.generator_matrix_constants.get_null_matrix(),
                            "settings": {},
                            "translation": self.command_context.generator_matrix_constants.get_null_matrix(),
                        }
                    },
                    "series": {
                        f"load_{area_id}": self.command_context.generator_matrix_constants.get_null_matrix(),
                    },
                },
                "misc-gen": {
                    f"miscgen-{area_id}": self.command_context.generator_matrix_constants.get_null_matrix()
                },
                "reserves": {
                    area_id: self.command_context.generator_matrix_constants.get_null_matrix()
                },
                "solar": {
                    "prepro": {
                        area_id: {
                            "conversion": self.command_context.generator_matrix_constants.get_prepro_conversion(),
                            "data": self.command_context.generator_matrix_constants.get_prepro_data(),
                            "k": self.command_context.generator_matrix_constants.get_null_matrix(),
                            "settings": {},
                            "translation": self.command_context.generator_matrix_constants.get_null_matrix(),
                        }
                    },
                    "series": {
                        f"solar_{area_id}": self.command_context.generator_matrix_constants.get_null_matrix(),
                    },
                },
                "thermal": {
                    "clusters": {area_id: {"list": {}}},
                    "areas": self._generate_new_thermal_areas_ini(
                        study_data,
                        area_id,
                        unservedenergycost=NodalOptimization.UNSERVERDDENERGYCOST.value,
                        spilledenergycost=NodalOptimization.SPILLEDENERGYCOST.value,
                    ),
                },
                "wind": {
                    "prepro": {
                        area_id: {
                            "conversion": self.command_context.generator_matrix_constants.get_prepro_conversion(),
                            "data": self.command_context.generator_matrix_constants.get_prepro_data(),
                            "k": self.command_context.generator_matrix_constants.get_null_matrix(),
                            "settings": {},
                            "translation": self.command_context.generator_matrix_constants.get_null_matrix(),
                        }
                    },
                    "series": {
                        f"wind_{area_id}": self.command_context.generator_matrix_constants.get_null_matrix()
                    },
                },
            }
        }

        if version > 650:
            get_or_create_section(hydro_config, "initialize reservoir date")[
                area_id
            ] = 0
            get_or_create_section(hydro_config, "leeway low")[area_id] = 1
            get_or_create_section(hydro_config, "leeway up")[area_id] = 1
            get_or_create_section(hydro_config, "pumping efficiency")[
                area_id
            ] = 1

            new_area_data["input"]["hydro"]["common"]["capacity"][
                f"creditmodulations_{area_id}"
            ] = (
                self.command_context.generator_matrix_constants.get_hydro_credit_modulations()
            )
            new_area_data["input"]["hydro"]["common"]["capacity"][
                f"inflowPattern_{area_id}"
            ] = (
                self.command_context.generator_matrix_constants.get_hydro_inflow_pattern()
            )
            new_area_data["input"]["hydro"]["common"]["capacity"][
                f"waterValues_{area_id}"
            ] = (
                self.command_context.generator_matrix_constants.get_null_matrix()
            )

        new_area_data["input"]["hydro"]["hydro"] = hydro_config

        study_data.tree.save(new_area_data)

        return CommandOutput(
            status=True, message=f"Area '{self.area_name}' created"
        )

    def revert(self, study_data: FileStudy) -> CommandOutput:
        raise NotImplementedError()
