from typing import Any, Optional, List, Tuple, Dict

from antarest.core.model import JSON
from antarest.study.storage.rawstudy.model.filesystem.config.model import (
    Area,
    transform_name_to_id,
    FileStudyTreeConfig,
)
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.common.default_values import (
    NodalOptimization,
    FilteringOptions,
)
from antarest.study.storage.variantstudy.business.utils import (
    get_or_create_section,
)
from antarest.study.storage.variantstudy.model.command.common import (
    CommandOutput,
    CommandName,
)
from antarest.study.storage.variantstudy.model.command.icommand import (
    ICommand,
    MATCH_SIGNATURE_SEPARATOR,
)
from antarest.study.storage.variantstudy.model.model import CommandDTO


class CreateArea(ICommand):
    area_name: str

    def __init__(self, **data: Any) -> None:
        super().__init__(
            command_name=CommandName.CREATE_AREA,
            version=1,
            **data,
        )

    def _generate_new_thermal_areas_ini(
        self,
        file_study: FileStudy,
        area_id: str,
        unserverdenergycost: Optional[float] = None,
        spilledenergycost: Optional[float] = None,
    ) -> JSON:
        new_areas: JSON = file_study.tree.get(
            url=["input", "thermal", "areas"]
        )
        if unserverdenergycost is not None:
            new_areas["unserverdenergycost"][area_id] = unserverdenergycost
        if spilledenergycost is not None:
            new_areas["spilledenergycost"][area_id] = spilledenergycost

        return new_areas

    def _apply_config(
        self, study_data: FileStudyTreeConfig
    ) -> Tuple[CommandOutput, Dict[str, Any]]:
        if self.command_context.generator_matrix_constants is None:
            raise ValueError()

        area_id = transform_name_to_id(self.area_name)

        if area_id in study_data.areas.keys():
            return (
                CommandOutput(
                    status=False,
                    message=f"Area '{self.area_name}' already exists and could not be created",
                ),
                dict(),
            )

        study_data.areas[area_id] = Area(
            name=self.area_name,
            links={},
            thermals=[],
            renewables=[],
            filters_synthesis=[],
            filters_year=[],
        )
        return (
            CommandOutput(
                status=True, message=f"Area '{self.area_name}' created"
            ),
            {"area_id": area_id},
        )

    def _apply(self, study_data: FileStudy) -> CommandOutput:
        output, data = self._apply_config(study_data.config)
        if not output.status:
            return output
        area_id = data["area_id"]
        version = study_data.config.version

        # fmt: off
        hydro_config = study_data.tree.get(["input", "hydro", "hydro"])
        get_or_create_section(hydro_config, "inter-daily-breakdown")[area_id] = 1
        get_or_create_section(hydro_config, "intra-daily-modulation")[area_id] = 24
        get_or_create_section(hydro_config, "inter-monthly-breakdown")[area_id] = 1
        # fmt: on

        new_area_data: JSON = {
            "input": {
                "areas": {
                    "list": [
                        area.name for area in study_data.config.areas.values()
                    ],
                    area_id: {
                        "optimization": {
                            "nodal optimization": {
                                "non-dispatchable-power": NodalOptimization.NON_DISPATCHABLE_POWER,
                                "dispatchable-hydro-power": NodalOptimization.DISPATCHABLE_HYDRO_POWER,
                                "other-dispatchable-power": NodalOptimization.OTHER_DISPATCHABLE_POWER,
                                "spread-unsupplied-energy-cost": NodalOptimization.SPREAD_UNSUPPLIED_ENERGY_COST,
                                "spread-spilled-energy-cost": NodalOptimization.SPREAD_SPILLED_ENERGY_COST,
                            },
                            "filtering": {
                                "filter-synthesis": FilteringOptions.FILTER_SYNTHESIS,
                                "filter-year-by-year": FilteringOptions.FILTER_YEAR_BY_YEAR,
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
                            "layerX": {"0": 0},
                            "layerY": {"0": 0},
                            "layerColor": {"0": "230 , 108 , 44"},
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
                        f"load_{area_id}": self.command_context.generator_matrix_constants.get_null_scenario_matrix(),
                    },
                },
                "misc-gen": {
                    f"miscgen-{area_id}": self.command_context.generator_matrix_constants.get_default_miscgen()
                },
                "reserves": {
                    area_id: self.command_context.generator_matrix_constants.get_default_reserves()
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
                        f"solar_{area_id}": self.command_context.generator_matrix_constants.get_null_scenario_matrix(),
                    },
                },
                "thermal": {
                    "clusters": {area_id: {"list": {}}},
                    "areas": self._generate_new_thermal_areas_ini(
                        study_data,
                        area_id,
                        unserverdenergycost=NodalOptimization.UNSERVERDDENERGYCOST,
                        spilledenergycost=NodalOptimization.SPILLEDENERGYCOST,
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
                        f"wind_{area_id}": self.command_context.generator_matrix_constants.get_null_scenario_matrix()
                    },
                },
            }
        }

        # Ensure the "annual" key exists in the hydro correlation configuration to avoid incorrect setup
        # fmt: off
        new_correlation = study_data.tree.get(["input", "hydro", "prepro", "correlation"])
        new_correlation.setdefault("annual", {})
        new_area_data["input"]["hydro"]["prepro"]["correlation"] = new_correlation
        # fmt: on

        if version > 650:
            # fmt: off
            get_or_create_section(hydro_config, "initialize reservoir date")[area_id] = 0
            get_or_create_section(hydro_config, "leeway low")[area_id] = 1
            get_or_create_section(hydro_config, "leeway up")[area_id] = 1
            get_or_create_section(hydro_config, "pumping efficiency")[area_id] = 1

            new_area_data["input"]["hydro"]["common"]["capacity"][f"creditmodulations_{area_id}"] = (
                self.command_context.generator_matrix_constants.get_hydro_credit_modulations()
            )
            new_area_data["input"]["hydro"]["common"]["capacity"][f"inflowPattern_{area_id}"] = (
                self.command_context.generator_matrix_constants.get_hydro_inflow_pattern()
            )
            new_area_data["input"]["hydro"]["common"]["capacity"][f"waterValues_{area_id}"] = (
                self.command_context.generator_matrix_constants.get_null_matrix()
            )
            # fmt: on

        if version >= 830:
            new_area_data["input"]["areas"][area_id]["adequacy_patch"] = {
                "adequacy-patch": {"adequacy-patch-mode": "outside"}
            }

        new_area_data["input"]["hydro"]["hydro"] = hydro_config

        # NOTE regarding the following configurations:
        # - ["input", "hydro", "prepro", "correlation"]
        # - ["input", "load", "prepro", "correlation"]
        # - ["input", "solar", "prepro", "correlation"]
        # - ["input", "wind", "prepro", "correlation"]
        # When creating a new area, we should not add a new correlation
        # value to the configuration because it does not store the values
        # of the diagonal (always equal to 1).

        study_data.tree.save(new_area_data)

        return output

    def to_dto(self) -> CommandDTO:
        return CommandDTO(
            action=CommandName.CREATE_AREA.value,
            args={"area_name": self.area_name},
        )

    def match_signature(self) -> str:
        return str(
            self.command_name.value
            + MATCH_SIGNATURE_SEPARATOR
            + self.area_name
        )

    def match(self, other: ICommand, equal: bool = False) -> bool:
        if not isinstance(other, CreateArea):
            return False
        return self.area_name == other.area_name

    def _create_diff(self, other: "ICommand") -> List["ICommand"]:
        return []

    def get_inner_matrices(self) -> List[str]:
        return []
