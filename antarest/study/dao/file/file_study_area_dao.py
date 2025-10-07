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
from abc import abstractmethod
from typing import Any, Dict, List

from typing_extensions import override

from antarest.core.model import JSON
from antarest.study.business.model.area_model import Area
from antarest.study.business.model.thermal_cluster_model import ThermalCluster
from antarest.study.dao.api.area_dao import AreaDao
from antarest.study.model import STUDY_VERSION_6_5, STUDY_VERSION_8_1, STUDY_VERSION_8_3, STUDY_VERSION_8_6
from antarest.study.storage.rawstudy.model.filesystem.config.identifier import transform_name_to_id
from antarest.study.storage.rawstudy.model.filesystem.config.model import AreaConfig, EnrModelling
from antarest.study.storage.rawstudy.model.filesystem.config.thermal import parse_thermal_cluster
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy


class FileStudyAreaDao(AreaDao):
    @abstractmethod
    def get_file_study(self) -> FileStudy:
        pass

    def _get_thermal_clusters(self, area_id: str) -> List[ThermalCluster]:
        """
        Retrieve thermal clusters for a specific area.

        Args:
            area_id: The area identifier.

        Returns:
            The list of thermal clusters for the area.
        """
        file_study = self.get_file_study()
        thermal_clusters_data = file_study.tree.get(["input", "thermal", "clusters", area_id, "list"])
        result = []
        for tid, obj in thermal_clusters_data.items():
            cluster_info = parse_thermal_cluster(file_study.config.version, obj)
            result.append(cluster_info)
        return result

    @override
    def get_all_areas(self) -> List[Area]:
        """
        Retrieve all physical areas of a study.
        """
        file_study = self.get_file_study()
        cfg_areas: Dict[str, AreaConfig] = file_study.config.areas
        return [
            Area(
                id=area_id,
                name=area.name,
                thermals=self._get_thermal_clusters(area_id),
            )
            for area_id, area in cfg_areas.items()
        ]

    @override
    def get_all_areas_ui_info(self) -> Dict[str, Any]:
        """
        Retrieve information about all areas' user interface (UI) from the study.

        Returns:
            Dictionary where keys are area IDs, and values are UI objects.

        Raises:
            ChildNotFoundError: if one of the Area IDs is not found in the configuration.
        """
        file_study = self.get_file_study()
        area_ids = list(file_study.config.areas)

        # If there is no ID, return an empty dictionary
        if not area_ids:
            return {}

        # Import AreaUIFileData here to avoid circular import
        from antarest.study.storage.rawstudy.model.filesystem.config.area import AreaUIFileData

        ui_info_map = file_study.tree.get(["input", "areas", ",".join(area_ids), "ui"])

        # If there is only one ID, the result is a single UI object
        # Otherwise, it's a dictionary with IDs as keys
        if len(area_ids) == 1:
            ui_info_map = {area_ids[0]: ui_info_map}

        # Convert to AreaUIFileData to ensure that the UI object is valid
        ui_info_map = {area_id: AreaUIFileData(**ui_info).to_config() for area_id, ui_info in ui_info_map.items()}

        return ui_info_map

    @override
    def save_area(self, area_name: str, command_context: Any) -> None:
        """
        Create a new area in the study with all necessary files and configurations.
        """
        study_data = self.get_file_study()
        config = study_data.config

        area_id = transform_name_to_id(area_name)

        if area_id in config.areas:
            raise ValueError(f"Area '{area_name}' already exists and could not be created")

        # Create area config in memory
        config.areas[area_id] = AreaConfig(
            name=area_name,
            links={},
            thermals=[],
            renewables=[],
            filters_synthesis=[],
            filters_year=[],
        )

        version = config.version

        # Update hydro configuration
        hydro_config = study_data.tree.get(["input", "hydro", "hydro"])
        hydro_config.setdefault("inter-daily-breakdown", {})[area_id] = 1
        hydro_config.setdefault("intra-daily-modulation", {})[area_id] = 24
        hydro_config.setdefault("inter-monthly-breakdown", {})[area_id] = 1

        # Get matrix constants
        null_matrix = command_context.generator_matrix_constants.get_null_matrix()

        # Build the new area data structure

        new_area_data: JSON = self._build_area_data_structure(
            area_id=area_id,
            area_name=area_name,
            config=config,
            version=version,
            hydro_config=hydro_config,
            command_context=command_context,
            null_matrix=null_matrix,
        )

        # Save to filesystem
        study_data.tree.save(new_area_data)

    def _build_area_data_structure(
        self,
        area_id: str,
        area_name: str,
        config: Any,
        version: Any,
        hydro_config: Dict[str, Any],
        command_context: Any,
        null_matrix: str,
    ) -> JSON:
        """Helper method to build the complete area data structure."""
        from antarest.study.storage.variantstudy.model.command.common import FilteringOptions
        from antarest.study.storage.variantstudy.model.command.create_area import NodalOptimization

        study_data = self.get_file_study()

        # Generate thermal areas ini
        thermal_areas_ini = study_data.tree.get(["input", "thermal", "areas"])
        thermal_areas_ini.setdefault("unserverdenergycost", {})[area_id] = NodalOptimization.UNSERVERDDENERGYCOST
        thermal_areas_ini.setdefault("spilledenergycost", {})[area_id] = NodalOptimization.SPILLEDENERGYCOST

        # Ensure the "annual" key exists in the hydro correlation configuration
        new_correlation = study_data.tree.get(["input", "hydro", "prepro", "correlation"])
        new_correlation.setdefault("annual", {})

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
                    "hydro": hydro_config,
                    "allocation": {area_id: {"[allocation]": {area_id: 1}}},
                    "common": {
                        "capacity": {
                            f"maxpower_{area_id}": command_context.generator_matrix_constants.get_hydro_max_power(
                                version=version
                            ),
                            f"reservoir_{area_id}": command_context.generator_matrix_constants.get_hydro_reservoir(
                                version=version
                            ),
                        }
                    },
                    "prepro": {
                        area_id: {
                            "energy": null_matrix,
                            "prepro": {"prepro": {"intermonthly-correlation": 0.5}},
                        },
                        "correlation": new_correlation,
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
                            "conversion": command_context.generator_matrix_constants.get_prepro_conversion(),
                            "data": command_context.generator_matrix_constants.get_prepro_data(),
                            "k": null_matrix,
                            "settings": {},
                            "translation": null_matrix,
                        }
                    },
                    "series": {
                        f"load_{area_id}": command_context.generator_matrix_constants.get_null_scenario_matrix(),
                    },
                },
                "misc-gen": {f"miscgen-{area_id}": command_context.generator_matrix_constants.get_default_miscgen()},
                "reserves": {area_id: command_context.generator_matrix_constants.get_default_reserves()},
                "solar": {
                    "prepro": {
                        area_id: {
                            "conversion": command_context.generator_matrix_constants.get_prepro_conversion(),
                            "data": command_context.generator_matrix_constants.get_prepro_data(),
                            "k": null_matrix,
                            "settings": {},
                            "translation": null_matrix,
                        }
                    },
                    "series": {
                        f"solar_{area_id}": command_context.generator_matrix_constants.get_null_scenario_matrix(),
                    },
                },
                "thermal": {
                    "clusters": {area_id: {"list": {}}},
                    "areas": thermal_areas_ini,
                },
                "wind": {
                    "prepro": {
                        area_id: {
                            "conversion": command_context.generator_matrix_constants.get_prepro_conversion(),
                            "data": command_context.generator_matrix_constants.get_prepro_data(),
                            "k": null_matrix,
                            "settings": {},
                            "translation": null_matrix,
                        }
                    },
                    "series": {
                        f"wind_{area_id}": command_context.generator_matrix_constants.get_null_scenario_matrix()
                    },
                },
            }
        }

        # Version-specific additions
        if version > STUDY_VERSION_6_5:
            hydro_config.setdefault("initialize reservoir date", {})[area_id] = 0
            hydro_config.setdefault("leeway low", {})[area_id] = 1
            hydro_config.setdefault("leeway up", {})[area_id] = 1
            hydro_config.setdefault("pumping efficiency", {})[area_id] = 1

            new_area_data["input"]["hydro"]["common"]["capacity"][f"creditmodulations_{area_id}"] = (
                command_context.generator_matrix_constants.get_hydro_credit_modulations()
            )
            new_area_data["input"]["hydro"]["common"]["capacity"][f"inflowPattern_{area_id}"] = (
                command_context.generator_matrix_constants.get_hydro_inflow_pattern()
            )
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

        return new_area_data

    @override
    def delete_area(self, area_id: str) -> None:
        """
        Delete an area from the study.
        """
        raise NotImplementedError("delete_area will be implemented next")
