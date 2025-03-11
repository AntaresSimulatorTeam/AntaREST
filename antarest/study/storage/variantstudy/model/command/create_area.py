# Copyright (c) 2025, RTE (https://www.rte-france.com)
#
# See AUTHORS.txt
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# SPDX-License-Identifier: MPL-2.0
#
# This file is part of the Antares project.

import typing as t

from pydantic import Field
from typing_extensions import override

from antarest.core.model import JSON
from antarest.study.model import STUDY_VERSION_6_5, STUDY_VERSION_8_1, STUDY_VERSION_8_3, STUDY_VERSION_8_6
from antarest.study.storage.rawstudy.model.filesystem.config.identifier import transform_name_to_id
from antarest.study.storage.rawstudy.model.filesystem.config.model import Area, EnrModelling, FileStudyTreeConfig
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.model.command.common import CommandName, CommandOutput, FilteringOptions
from antarest.study.storage.variantstudy.model.command.icommand import MATCH_SIGNATURE_SEPARATOR, ICommand
from antarest.study.storage.variantstudy.model.command_listener.command_listener import ICommandListener
from antarest.study.storage.variantstudy.model.model import CommandDTO


# noinspection SpellCheckingInspection
def _generate_new_thermal_areas_ini(
    file_study: FileStudy,
    area_id: str,
    *,
    unserverdenergycost: float,
    spilledenergycost: float,
) -> JSON:
    new_areas: JSON = file_study.tree.get(["input", "thermal", "areas"])
    if unserverdenergycost is not None:
        new_areas.setdefault("unserverdenergycost", {})[area_id] = unserverdenergycost
    if spilledenergycost is not None:
        new_areas.setdefault("spilledenergycost", {})[area_id] = spilledenergycost
    return new_areas


class NodalOptimization:
    NON_DISPATCHABLE_POWER: bool = True
    DISPATCHABLE_HYDRO_POWER: bool = True
    OTHER_DISPATCHABLE_POWER: bool = True
    SPREAD_UNSUPPLIED_ENERGY_COST: float = 0.000000
    SPREAD_SPILLED_ENERGY_COST: float = 0.000000
    UNSERVERDDENERGYCOST: float = 0.000000
    SPILLEDENERGYCOST: float = 0.000000


class CreateArea(ICommand):
    """
    Command used to create a new area in the study.
    """

    # Overloaded metadata
    # ===================

    command_name: CommandName = CommandName.CREATE_AREA

    # Command parameters
    # ==================

    area_name: str

    # The `metadata` attribute is added to ensure upward compatibility with previous versions.
    # Ideally, this attribute should be of type `PatchArea`, but as it is not used,
    # we choose to declare it as an empty dictionary.
    # fixme: remove this attribute in the next version if it is not used by the "Script R" team,
    #  or if we don't want to support this feature.
    metadata: t.Dict[str, str] = Field(default_factory=dict, description="Area metadata: country and tag list")

    @override
    def _apply_config(self, study_data: FileStudyTreeConfig) -> t.Tuple[CommandOutput, t.Dict[str, t.Any]]:
        if self.command_context.generator_matrix_constants is None:
            raise ValueError()

        area_id = transform_name_to_id(self.area_name)

        if area_id in study_data.areas.keys():
            return (
                CommandOutput(
                    status=False,
                    message=f"Area '{self.area_name}' already exists and could not be created",
                ),
                {},
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
            CommandOutput(status=True, message=f"Area '{self.area_name}' created"),
            {"area_id": area_id},
        )

    @override
    def _apply(self, study_data: FileStudy, listener: t.Optional[ICommandListener] = None) -> CommandOutput:
        config = study_data.config

        output, data = self._apply_config(config)
        if not output.status:
            return output
        area_id = data["area_id"]
        version = config.version

        hydro_config = study_data.tree.get(["input", "hydro", "hydro"])
        hydro_config.setdefault("inter-daily-breakdown", {})[area_id] = 1
        hydro_config.setdefault("inter-daily-breakdown", {})[area_id] = 1
        hydro_config.setdefault("intra-daily-modulation", {})[area_id] = 24
        hydro_config.setdefault("inter-monthly-breakdown", {})[area_id] = 1

        null_matrix = self.command_context.generator_matrix_constants.get_null_matrix()

        new_area_data: JSON = {
            "input": {
                "areas": {
                    "list": [area.name for area in config.areas.values()],
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
                            "energy": null_matrix,
                            "prepro": {"prepro": {"intermonthly-correlation": 0.5}},
                        },
                    },
                    "series": {
                        area_id: {
                            "mod": null_matrix,
                            "ror": null_matrix,
                        },
                    },
                },
                "links": {area_id: {"properties": {}}},
                "load": {
                    "prepro": {
                        area_id: {
                            "conversion": self.command_context.generator_matrix_constants.get_prepro_conversion(),
                            "data": self.command_context.generator_matrix_constants.get_prepro_data(),
                            "k": null_matrix,
                            "settings": {},
                            "translation": null_matrix,
                        }
                    },
                    "series": {
                        f"load_{area_id}": self.command_context.generator_matrix_constants.get_null_scenario_matrix(),
                    },
                },
                "misc-gen": {
                    f"miscgen-{area_id}": self.command_context.generator_matrix_constants.get_default_miscgen()
                },
                "reserves": {area_id: self.command_context.generator_matrix_constants.get_default_reserves()},
                "solar": {
                    "prepro": {
                        area_id: {
                            "conversion": self.command_context.generator_matrix_constants.get_prepro_conversion(),
                            "data": self.command_context.generator_matrix_constants.get_prepro_data(),
                            "k": null_matrix,
                            "settings": {},
                            "translation": null_matrix,
                        }
                    },
                    "series": {
                        f"solar_{area_id}": self.command_context.generator_matrix_constants.get_null_scenario_matrix(),
                    },
                },
                "thermal": {
                    "clusters": {area_id: {"list": {}}},
                    "areas": _generate_new_thermal_areas_ini(
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
                            "k": null_matrix,
                            "settings": {},
                            "translation": null_matrix,
                        }
                    },
                    "series": {
                        f"wind_{area_id}": self.command_context.generator_matrix_constants.get_null_scenario_matrix()
                    },
                },
            }
        }

        # Ensure the "annual" key exists in the hydro correlation configuration to avoid incorrect setup

        new_correlation = study_data.tree.get(["input", "hydro", "prepro", "correlation"])
        new_correlation.setdefault("annual", {})
        new_area_data["input"]["hydro"]["prepro"]["correlation"] = new_correlation

        if version > STUDY_VERSION_6_5:
            hydro_config.setdefault("initialize reservoir date", {})[area_id] = 0
            hydro_config.setdefault("leeway low", {})[area_id] = 1
            hydro_config.setdefault("leeway up", {})[area_id] = 1
            hydro_config.setdefault("pumping efficiency", {})[area_id] = 1

            new_area_data["input"]["hydro"]["common"]["capacity"][
                f"creditmodulations_{area_id}"
            ] = self.command_context.generator_matrix_constants.get_hydro_credit_modulations()
            new_area_data["input"]["hydro"]["common"]["capacity"][
                f"inflowPattern_{area_id}"
            ] = self.command_context.generator_matrix_constants.get_hydro_inflow_pattern()
            new_area_data["input"]["hydro"]["common"]["capacity"][f"waterValues_{area_id}"] = null_matrix

        has_renewables = version >= STUDY_VERSION_8_1 and EnrModelling(config.enr_modelling) == EnrModelling.CLUSTERS
        if has_renewables:
            new_area_data["input"]["renewables"] = {"clusters": {area_id: {"list": {}}}}

        if version >= STUDY_VERSION_8_3:
            new_area_data["input"]["areas"][area_id]["adequacy_patch"] = {
                "adequacy-patch": {"adequacy-patch-mode": "outside"}
            }

        if version >= STUDY_VERSION_8_6:
            new_area_data["input"]["st-storage"] = {"clusters": {area_id: {"list": {}}}}
            new_area_data["input"]["hydro"]["series"][area_id]["mingen"] = null_matrix

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

    @override
    def to_dto(self) -> CommandDTO:
        return CommandDTO(
            action=CommandName.CREATE_AREA.value, args={"area_name": self.area_name}, study_version=self.study_version
        )

    @override
    def get_inner_matrices(self) -> t.List[str]:
        return []
