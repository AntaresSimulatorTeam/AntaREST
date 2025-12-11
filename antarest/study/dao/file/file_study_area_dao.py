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
import contextlib
import logging
import re
import typing as t
from abc import abstractmethod
from typing import Any, Dict, List

import pandas as pd
from typing_extensions import override

from antarest.core.exceptions import ChildNotFoundError, LayerNotFound, ReferencedObjectDeletionNotAllowed
from antarest.core.model import JSON
from antarest.study.business.model.area_model import AreaInfo, AreaUI, AreaUIData
from antarest.study.business.model.binding_constraint_model import ClusterTerm, LinkTerm
from antarest.study.dao.api.area_dao import AreaDao
from antarest.study.model import (
    STUDY_VERSION_6_5,
    STUDY_VERSION_8_1,
    STUDY_VERSION_8_2,
    STUDY_VERSION_8_6,
    STUDY_VERSION_9_2,
)
from antarest.study.storage.rawstudy.model.filesystem.config.identifier import transform_name_to_id
from antarest.study.storage.rawstudy.model.filesystem.config.model import AreaConfig, EnrModelling, FileStudyTreeConfig
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy

if t.TYPE_CHECKING:
    from antarest.study.dao.file.file_study_dao import FileStudyTreeDao


class FileStudyAreaDao(AreaDao):
    @abstractmethod
    def get_file_study(self) -> FileStudy:
        pass

    @abstractmethod
    def get_impl(self) -> "FileStudyTreeDao":
        pass

    @override
    def get_all_areas_info(self) -> List[AreaInfo]:
        """
        Retrieve all physical areas of a study.
        """
        file_study = self.get_file_study()
        cfg_areas: Dict[str, AreaConfig] = file_study.config.areas
        return [
            AreaInfo(
                id=area_id,
                name=area.name,
                thermals=list(self.get_impl().get_all_thermals_for_area(area_id)),
            )
            for area_id, area in cfg_areas.items()
        ]

    @override
    def get_all_areas_ui_info(self) -> Dict[str, AreaUIData]:
        """
        Retrieve information about all areas' user interface (UI) from the study.

        Returns:
            Dictionary where keys are area IDs, and values are AreaUIData objects.

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

        # Convert to AreaUIFileData to ensure that the UI object is valid, then to Pydantic model
        return {
            area_id: AreaUIData.model_validate(AreaUIFileData(**ui_info).to_config())
            for area_id, ui_info in ui_info_map.items()
        }

    @override
    def get_area_ui(self, area_id: str, layer: str = "0") -> AreaUI:
        """
        Retrieve UI information for a specific area and layer.

        Args:
            area_id: The area identifier.
            layer: The layer identifier (typically "0", "1", etc"). Defaults to "0".

        Returns:
            The UI properties for the area (x, y, color_rgb).

        Raises:
            ChildNotFoundError: If the area does not exist.
        """
        file_study = self.get_file_study()

        # Check if area exists in config
        if area_id not in file_study.config.areas:
            from antarest.core.exceptions import AreaNotFound

            raise AreaNotFound(area_id)

        # Import AreaUIFileData here to avoid circular import
        from antarest.study.storage.rawstudy.model.filesystem.config.area import AreaUIFileData

        # Get the UI info for this specific area
        ui_info = file_study.tree.get(["input", "areas", area_id, "ui"])

        # Convert to AreaUIFileData to ensure that the UI object is valid
        area_ui_data = AreaUIFileData(**ui_info)

        # Extract the UI for the specific layer
        layer_int = int(layer)
        if layer_int in area_ui_data.layer_styles:
            style = area_ui_data.layer_styles[layer_int]
            x = style.x
            y = style.y
            color_rgb = (style.color_r, style.color_g, style.color_b)
        else:
            # Fall back to default style
            x = area_ui_data.style.x
            y = area_ui_data.style.y
            color_rgb = (area_ui_data.style.color_r, area_ui_data.style.color_g, area_ui_data.style.color_b)

        return AreaUI(x=x, y=y, color_rgb=color_rgb)

    @override
    def get_load(self, area_id: str) -> pd.DataFrame:
        return self.get_impl().get_matrix(["input", "load", "series", f"load_{area_id}"])

    @override
    def get_misc_gen(self, area_id: str) -> pd.DataFrame:
        return self.get_impl().get_matrix(["input", "misc-gen", f"miscgen-{area_id}"])

    @override
    def get_reserves(self, area_id: str) -> pd.DataFrame:
        return self.get_impl().get_matrix(["input", "reserves", area_id])

    @override
    def get_solar(self, area_id: str) -> pd.DataFrame:
        return self.get_impl().get_matrix(["input", "solar", "series", f"solar_{area_id}"])

    @override
    def get_wind(self, area_id: str) -> pd.DataFrame:
        return self.get_impl().get_matrix(["input", "wind", "series", f"wind_{area_id}"])

    @override
    def save_area(self, area_name: str) -> None:
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

        # Build the new area data structure
        new_area_data: JSON = self._build_area_data_structure(area_id=area_id, config=config)

        # Save to filesystem
        study_data.tree.save(new_area_data)

    def _build_area_data_structure(self, area_id: str, config: FileStudyTreeConfig) -> JSON:
        generator_matrix_constants = self.get_impl()._generator_matrix_constants
        null_matrix = generator_matrix_constants.get_null_matrix()
        prepro_data = {
            area_id: {
                "conversion": generator_matrix_constants.get_prepro_conversion(),
                "data": generator_matrix_constants.get_prepro_data(),
                "k": null_matrix,
                "settings": {},
                "translation": null_matrix,
            }
        }

        new_area_data: JSON = {
            "input": {
                "areas": {"list": [area.name for area in config.areas.values()]},
                "links": {area_id: {"properties": {}}},
                "load": {"prepro": prepro_data},
                "solar": {"prepro": prepro_data},
                "thermal": {"clusters": {area_id: {"list": {}}}},
                "wind": {"prepro": prepro_data},
            }
        }

        # Version-specific additions
        version = config.version
        has_renewables = version >= STUDY_VERSION_8_1 and EnrModelling(config.enr_modelling) == EnrModelling.CLUSTERS
        if has_renewables:
            new_area_data["input"]["renewables"] = {"clusters": {area_id: {"list": {}}}}

        if version >= STUDY_VERSION_8_6:
            new_area_data["input"]["st-storage"] = {"clusters": {area_id: {"list": {}}}}

        return new_area_data

    @override
    def delete_area(self, area_id: str) -> None:
        """
        Delete an area from the study.
        Removes all associated files, configurations, and references.
        """
        logger = logging.getLogger(__name__)

        study_data = self.get_file_study()

        # Check that the area is not referenced in any binding constraint
        referencing_binding_constraints = []
        for bc in study_data.config.bindings:
            for term in bc.terms:
                data = term.data
                if (isinstance(data, ClusterTerm) and data.area == area_id) or (
                    isinstance(data, LinkTerm) and (data.area1 == area_id or data.area2 == area_id)
                ):
                    referencing_binding_constraints.append(bc)
                    break
        if referencing_binding_constraints:
            binding_ids = [bc.id for bc in referencing_binding_constraints]
            raise ReferencedObjectDeletionNotAllowed(area_id, binding_ids, object_type="Area")

        # Delete all area files from the tree
        self._delete_area_files(area_id, study_data)

        # Clean up all references to the area
        self._remove_area_from_links(area_id, study_data, logger)
        self._remove_area_from_correlation_matrices(area_id, study_data)
        self._remove_area_from_hydro_allocation(area_id, study_data)
        self._remove_area_from_districts(area_id, study_data)
        self._remove_area_from_scenario_builder(area_id, study_data)

        # Remove from config
        self._remove_from_config(area_id, study_data.config)

        # Update area list
        new_area_data: JSON = {"input": {"areas": {"list": [area.name for area in study_data.config.areas.values()]}}}
        study_data.tree.save(new_area_data)

    def _delete_area_files(self, area_id: str, study_data: Any) -> None:
        """Delete all files associated with an area from the tree."""
        # Delete basic area files
        study_data.tree.delete(["input", "areas", area_id])
        study_data.tree.delete(["input", "hydro", "common", "capacity", f"maxpower_{area_id}"])
        study_data.tree.delete(["input", "hydro", "common", "capacity", f"reservoir_{area_id}"])
        study_data.tree.delete(["input", "hydro", "prepro", area_id])
        study_data.tree.delete(["input", "hydro", "series", area_id])
        study_data.tree.delete(["input", "hydro", "hydro", "inter-daily-breakdown", area_id])
        study_data.tree.delete(["input", "hydro", "hydro", "intra-daily-modulation", area_id])
        study_data.tree.delete(["input", "hydro", "hydro", "inter-monthly-breakdown", area_id])
        study_data.tree.delete(["input", "load", "prepro", area_id])
        study_data.tree.delete(["input", "load", "series", f"load_{area_id}"])
        study_data.tree.delete(["input", "misc-gen", f"miscgen-{area_id}"])
        study_data.tree.delete(["input", "reserves", area_id])
        study_data.tree.delete(["input", "solar", "prepro", area_id])
        study_data.tree.delete(["input", "solar", "series", f"solar_{area_id}"])
        study_data.tree.delete(["input", "thermal", "clusters", area_id])
        study_data.tree.delete(["input", "thermal", "prepro", area_id])
        study_data.tree.delete(["input", "thermal", "series", area_id])
        study_data.tree.delete(["input", "thermal", "areas", "unserverdenergycost", area_id])
        study_data.tree.delete(["input", "thermal", "areas", "spilledenergycost", area_id])
        study_data.tree.delete(["input", "wind", "prepro", area_id])
        study_data.tree.delete(["input", "wind", "series", f"wind_{area_id}"])
        study_data.tree.delete(["input", "links", area_id])

        # Version-specific deletions
        study_version = study_data.config.version
        if study_version > STUDY_VERSION_6_5:
            study_data.tree.delete(["input", "hydro", "hydro", "initialize reservoir date", area_id])
            study_data.tree.delete(["input", "hydro", "hydro", "leeway low", area_id])
            study_data.tree.delete(["input", "hydro", "hydro", "leeway up", area_id])
            study_data.tree.delete(["input", "hydro", "hydro", "pumping efficiency", area_id])
            study_data.tree.delete(["input", "hydro", "hydro", "reservoir", area_id])
            study_data.tree.delete(["input", "hydro", "hydro", "reservoir capacity", area_id])
            study_data.tree.delete(["input", "hydro", "hydro", "follow load", area_id])
            study_data.tree.delete(["input", "hydro", "hydro", "use water", area_id])
            study_data.tree.delete(["input", "hydro", "hydro", "hard bounds", area_id])
            study_data.tree.delete(["input", "hydro", "hydro", "use heuristic", area_id])
            study_data.tree.delete(["input", "hydro", "hydro", "power to level", area_id])
            study_data.tree.delete(["input", "hydro", "hydro", "use leeway", area_id])
            study_data.tree.delete(["input", "hydro", "common", "capacity", f"creditmodulations_{area_id}"])
            study_data.tree.delete(["input", "hydro", "common", "capacity", f"inflowPattern_{area_id}"])
            study_data.tree.delete(["input", "hydro", "common", "capacity", f"waterValues_{area_id}"])

        if study_version >= STUDY_VERSION_8_1:
            with contextlib.suppress(ChildNotFoundError):
                study_data.tree.delete(["input", "renewables", "clusters", area_id])
                study_data.tree.delete(["input", "renewables", "series", area_id])

        if study_version >= STUDY_VERSION_8_6:
            study_data.tree.delete(["input", "st-storage", "clusters", area_id])
            study_data.tree.delete(["input", "st-storage", "series", area_id])

        if study_version > STUDY_VERSION_9_2:
            study_data.tree.delete(["input", "hydro", "hydro", "overflow spilled cost difference", area_id])

        if (study_data.tree.config.path / "user" / "ts-generator-output" / "thermal" / area_id).exists():
            study_data.tree.delete(["user", "ts-generator-output", "thermal", area_id])

    def _remove_area_from_links(self, area_id: str, study_data: Any, logger: Any) -> None:
        """Remove all links associated with the area."""

        for area_name, area in study_data.config.areas.items():
            for link in area.links:
                if link == area_id:
                    study_data.tree.delete(["input", "links", area_name, "properties", area_id])
                    try:
                        if study_data.config.version < STUDY_VERSION_8_2:
                            study_data.tree.delete(["input", "links", area_name, area_id])
                        else:
                            study_data.tree.delete(["input", "links", area_name, f"{area_id}_parameters"])
                            study_data.tree.delete(["input", "links", area_name, "capacities", f"{area_id}_indirect"])
                            study_data.tree.delete(["input", "links", area_name, "capacities", f"{area_id}_direct"])
                    except ChildNotFoundError as e:
                        logger.warning(
                            f"Failed to clean link data when deleting area {area_id}"
                            f" in study {study_data.config.study_id}",
                            exc_info=e,
                        )

    def _remove_area_from_correlation_matrices(self, area_id: str, study_data: Any) -> None:
        """Remove the area from correlation matrices."""
        url = ["input", "hydro", "prepro", "correlation"]
        correlation_cfg = study_data.tree.get(url)
        for section, correlation in correlation_cfg.items():
            if section == "general":
                continue
            for key in list(correlation):
                a1, a2 = key.split("%")
                if a1 == area_id or a2 == area_id:
                    del correlation[key]
        study_data.tree.save(correlation_cfg, url)

    def _remove_area_from_hydro_allocation(self, area_id: str, study_data: Any) -> None:
        """Remove the area from hydraulic allocation configuration."""
        study_data.tree.delete(["input", "hydro", "allocation", area_id])
        allocation_cfg = study_data.tree.get(["input", "hydro", "allocation", "*"])
        if len(allocation_cfg) == 1:
            allocation_cfg = {area_id: allocation_cfg}
        allocation_cfg.pop(area_id, None)
        for prod_area, allocation_dict in allocation_cfg.items():
            for name, allocations in allocation_dict.items():
                allocations.pop(area_id, None)
        study_data.tree.save(allocation_cfg, ["input", "hydro", "allocation"])

    def _remove_area_from_districts(self, area_id: str, study_data: Any) -> None:
        """Remove the area from all districts."""
        districts = study_data.tree.get(["input", "areas", "sets"])
        for district in districts.values():
            if district.get("+", None):
                with contextlib.suppress(ValueError):
                    district["+"].remove(area_id)
            elif district.get("-", None):
                with contextlib.suppress(ValueError):
                    district["-"].remove(area_id)

        study_data.tree.save(districts, ["input", "areas", "sets"])

    def _remove_area_from_scenario_builder(self, area_id: str, study_data: Any) -> None:
        """Remove the area from scenario builder configuration."""
        rulesets = study_data.tree.get(["settings", "scenariobuilder"])

        area_keys = {"l", "h", "w", "s", "t", "r", "hl", "hfl", "hgp"}
        link_keys = {"ntc"}
        for ruleset in rulesets.values():
            for key in list(ruleset):
                symbol, *parts = key.split(",")
                if (symbol in area_keys and parts[0] == area_id) or (
                    symbol in link_keys and (parts[0] == area_id or parts[1] == area_id)
                ):
                    del ruleset[key]

        study_data.tree.save(rulesets, ["settings", "scenariobuilder"])

    def _remove_from_config(self, area_id: str, config: Any) -> None:
        """Remove the area from the configuration and clean up references."""
        del config.areas[area_id]

        link_to_remove = [
            (area_name, link) for area_name, area in config.areas.items() for link in area.links if link == area_id
        ]
        for area_name, link in link_to_remove:
            del config.areas[area_name].links[link]

        for id_, set_ in config.districts.items():
            if set_.add_areas and area_id in set_.add_areas:
                with contextlib.suppress(ValueError):
                    set_.add_areas.remove(area_id)
                    config.districts[id_] = set_
            if set_.subtract_areas and area_id in set_.subtract_areas:
                with contextlib.suppress(ValueError):
                    set_.subtract_areas.remove(area_id)
                    config.districts[id_] = set_

    @override
    def save_area_ui(self, area_id: str, layer: str, area_ui: AreaUI) -> None:
        """
        Save an area's UI properties (position and color) for a specific layer.
        """
        study_data = self.get_file_study()
        current_area = study_data.tree.get(["input", "areas", area_id, "ui"])
        layer_int = int(layer)

        # Initialize sections if missing (happens when creating the area)
        for section in ["layerX", "layerY", "layerColor"]:
            current_area.setdefault(section, {})
        if "ui" not in current_area:
            current_area["ui"] = {"layers": 0}

        # Save all UI properties
        current_area["layerX"][layer] = area_ui.x
        if layer_int == 0:
            current_area["ui"]["x"] = area_ui.x

        current_area["layerY"][layer] = area_ui.y
        if layer_int == 0:
            current_area["ui"]["y"] = area_ui.y

        r, g, b = area_ui.color_rgb
        current_area["layerColor"][layer] = f"{r}, {g}, {b}"
        if layer_int == 0:
            current_area["ui"]["color_r"] = r
            current_area["ui"]["color_g"] = g
            current_area["ui"]["color_b"] = b

        study_data.tree.save(current_area, ["input", "areas", area_id, "ui"])

    @staticmethod
    def _get_area_layers(area_uis: Dict[str, Any], area: str) -> List[str]:
        """Extract the list of layers from an area's UI configuration."""
        if area in area_uis and "ui" in area_uis[area] and "layers" in area_uis[area]["ui"]:
            layers_str = str(area_uis[area]["ui"]["layers"]).strip()
            return re.split(r"\s+", layers_str) if layers_str else []
        return []

    @override
    def save_layer_areas(self, layer_id: str, area_ids: List[str]) -> None:
        study_data = self.get_file_study()

        # Verify that the layer exists
        layers = study_data.tree.get(["layers", "layers", "layers"])
        if layer_id not in [str(layer) for layer in list(layers.keys())]:
            raise LayerNotFound

        # Get all areas UI configuration
        areas_ui = study_data.tree.get(["input", "areas", ",".join(study_data.config.areas), "ui"])

        # Standardize 'areas_ui' to a dictionary format even if only one area exists
        cfg_areas = list(study_data.config.areas)
        if len(cfg_areas) == 1:
            areas_ui = {cfg_areas[0]: areas_ui}

        # Determine which areas currently have this layer
        existing_areas = [
            area for area in areas_ui if "ui" in areas_ui[area] and layer_id in self._get_area_layers(areas_ui, area)
        ]

        # Calculate areas to add and remove
        to_remove_areas = [area for area in existing_areas if area not in area_ids]
        to_add_areas = [area for area in area_ids if area not in existing_areas]

        # Remove layer from areas
        for area in to_remove_areas:
            area_layers = self._get_area_layers(areas_ui, area)
            if layer_id in areas_ui[area]["layerX"]:
                del areas_ui[area]["layerX"][layer_id]
            if layer_id in areas_ui[area]["layerY"]:
                del areas_ui[area]["layerY"][layer_id]
            if layer_id in area_layers:
                areas_ui[area]["ui"]["layers"] = " ".join([layer for layer in area_layers if layer != layer_id])

        # Add layer to areas
        for area in to_add_areas:
            area_layers = self._get_area_layers(areas_ui, area)
            if layer_id not in areas_ui[area]["layerX"]:
                areas_ui[area]["layerX"][layer_id] = areas_ui[area]["ui"]["x"]
            if layer_id not in areas_ui[area]["layerY"]:
                areas_ui[area]["layerY"][layer_id] = areas_ui[area]["ui"]["y"]
            if layer_id not in area_layers:
                areas_ui[area]["ui"]["layers"] = " ".join(area_layers + [layer_id])

        # Save all modified areas
        for area in to_remove_areas + to_add_areas:
            study_data.tree.save(areas_ui[area], ["input", "areas", area, "ui"])

    @override
    def save_load(self, area_id: str, series_id: str) -> None:
        study_data = self.get_file_study()
        study_data.tree.save(series_id, ["input", "load", "series", f"load_{area_id}"])

    @override
    def save_misc_gen(self, area_id: str, series_id: str) -> None:
        study_data = self.get_file_study()
        study_data.tree.save(series_id, ["input", "misc-gen", f"miscgen-{area_id}"])

    @override
    def save_reserves(self, area_id: str, series_id: str) -> None:
        study_data = self.get_file_study()
        study_data.tree.save(series_id, ["input", "reserves", area_id])

    @override
    def save_solar(self, area_id: str, series_id: str) -> None:
        study_data = self.get_file_study()
        study_data.tree.save(series_id, ["input", "solar", "series", f"solar_{area_id}"])

    @override
    def save_wind(self, area_id: str, series_id: str) -> None:
        study_data = self.get_file_study()
        study_data.tree.save(series_id, ["input", "wind", "series", f"wind_{area_id}"])
