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

import enum
import re
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Set

from pydantic import Field

from antarest.core.serde import AntaresBaseModel
from antarest.study.business.all_optional_meta import all_optional_model, camel_case_model
from antarest.study.business.model.thermal_cluster_model import ThermalClusterOutput
from antarest.study.storage.rawstudy.model.filesystem.config.area import (
    AdequacyPathProperties,
    AreaFolder,
    OptimizationProperties,
)


class AreaType(enum.Enum):
    AREA = "AREA"
    DISTRICT = "DISTRICT"


class AreaProperties(AntaresBaseModel):
    thermal_properties: Dict[str, Any]
    filtering_props: Dict[str, Any]
    optim_properties: Dict[str, Any]
    adequacy_patch_property: Dict[str, Any]


FILTER_OPTIONS = ["hourly", "daily", "weekly", "monthly", "annual"]


def sort_filter_options(options: Iterable[str]) -> List[str]:
    return sorted(
        options,
        key=lambda x: FILTER_OPTIONS.index(x),
    )


def encode_filter(value: str) -> Set[str]:
    stripped = value.strip()
    return set(re.split(r"\s*,\s*", stripped) if stripped else [])


def decode_filter(encoded_value: Set[str]) -> str:
    if isinstance(encoded_value, str):
        return encoded_value
    return ", ".join(sort_filter_options(encoded_value))


def build_area_properties(properties: Dict[str, Any]) -> AreaProperties:
    thermal_properties = {}
    if "energy_cost_unsupplied" in properties:
        thermal_properties.update({"unserverdenergycost": properties["energy_cost_unsupplied"]})
    if "energy_cost_spilled" in properties:
        thermal_properties.update({"spilledenergycost": properties["energy_cost_spilled"]})

    filtering_props = {}
    if "filter_synthesis" in properties:
        filtering_props.update({"filter-synthesis": properties["filter_synthesis"]})
    if "filter_by_year" in properties:
        filtering_props.update({"filter-year-by-year": properties["filter_by_year"]})

    optim_properties = {}
    if key := next((k for k in ["non_dispatch_power", "non_dispatchable_power"] if k in properties), None):
        optim_properties.update({"non-dispatchable-power": properties[key]})
    if key := next((k for k in ["dispatch_hydro_power", "dispatchable_hydro_power"] if k in properties), None):
        optim_properties.update({"dispatchable-hydro-power": properties[key]})
    if key := next((k for k in ["other_dispatch_power", "other_dispatchable_power"] if k in properties), None):
        optim_properties.update({"other-dispatchable-power": properties[key]})
    if "spread_unsupplied_energy_cost" in properties:
        optim_properties.update({"spread-unsupplied-energy-cost": properties["spread_unsupplied_energy_cost"]})
    if "spread_spilled_energy_cost" in properties:
        optim_properties.update({"spread-spilled-energy-cost": properties["spread_spilled_energy_cost"]})

    adequacy_patch_property = {}
    if "adequacy_patch_mode" in properties:
        adequacy_patch_property.update({"adequacy-patch-mode": properties["adequacy_patch_mode"]})

    return AreaProperties(
        thermal_properties=thermal_properties,
        filtering_props=filtering_props,
        optim_properties=optim_properties,
        adequacy_patch_property=adequacy_patch_property,
    )


class AreaCreationDTO(AntaresBaseModel):
    name: str
    type: AreaType
    set: Optional[List[str]] = None


class AreaInfoDTO(AreaCreationDTO):
    id: str
    thermals: Optional[List[ThermalClusterOutput]] = None


class LayerInfoDTO(AntaresBaseModel):
    id: str
    name: str
    areas: List[str]


class UpdateAreaUi(AntaresBaseModel, extra="forbid", populate_by_name=True):
    x: int = Field(title="X position")
    y: int = Field(title="Y position")
    color_rgb: Sequence[int] = Field(title="RGB color", alias="colorRgb")
    layer_x: Mapping[int, int] = Field(default_factory=dict, title="X position of each layer", alias="layerX")
    layer_y: Mapping[int, int] = Field(default_factory=dict, title="Y position of each layer", alias="layerY")
    layer_color: Mapping[int, str] = Field(default_factory=dict, title="Color of each layer", alias="layerColor")


# noinspection SpellCheckingInspection
class _BaseAreaDTO(
    OptimizationProperties.FilteringSection,
    OptimizationProperties.ModalOptimizationSection,
    AdequacyPathProperties.AdequacyPathSection,
    extra="forbid",
    validate_assignment=True,
    populate_by_name=True,
):
    """
    Represents an area output.

    Aggregates the fields of the `OptimizationProperties` and `AdequacyPathProperties` classes,
    but without the `UIProperties` fields.

    Add the fields extracted from the `/input/thermal/areas.ini` information:

    - `average_unsupplied_energy_cost` is extracted from `unserverd_energy_cost`,
    - `average_spilled_energy_cost` is extracted from `spilled_energy_cost`.
    """

    average_unsupplied_energy_cost: float = Field(0.0, description="average unserverd energy cost (€/MWh)")
    average_spilled_energy_cost: float = Field(0.0, description="average spilled energy cost (€/MWh)")


# noinspection SpellCheckingInspection
@all_optional_model
@camel_case_model
class AreaOutput(_BaseAreaDTO):
    """
    DTO object use to get the area information using a flat structure.
    """

    @classmethod
    def from_model(
        cls,
        area_folder: AreaFolder,
        *,
        average_unsupplied_energy_cost: float,
        average_spilled_energy_cost: float,
    ) -> "AreaOutput":
        """
        Creates a `GetAreaDTO` object from configuration data.

        Args:
            area_folder: Configuration data read from the `/input/areas/<area>` information.
            average_unsupplied_energy_cost: Unserverd energy cost (€/MWh).
            average_spilled_energy_cost: Spilled energy cost (€/MWh).
        Returns:
            The `GetAreaDTO` object.
        """
        obj = {
            "average_unsupplied_energy_cost": average_unsupplied_energy_cost,
            "average_spilled_energy_cost": average_spilled_energy_cost,
            **area_folder.optimization.filtering.model_dump(mode="json", by_alias=False),
            **area_folder.optimization.nodal_optimization.model_dump(mode="json", by_alias=False),
            # adequacy_patch is only available if study version >= 830.
            **(
                area_folder.adequacy_patch.adequacy_patch.model_dump(mode="json", by_alias=False)
                if area_folder.adequacy_patch
                else {}
            ),
        }
        return cls(**obj)

    def _to_optimization(self) -> OptimizationProperties:
        obj = {name: getattr(self, name) for name in OptimizationProperties.FilteringSection.model_fields}
        filtering_section = OptimizationProperties.FilteringSection(**obj)
        obj = {name: getattr(self, name) for name in OptimizationProperties.ModalOptimizationSection.model_fields}
        nodal_optimization_section = OptimizationProperties.ModalOptimizationSection(**obj)
        args = {"filtering": filtering_section, "nodal_optimization": nodal_optimization_section}
        return OptimizationProperties.model_validate(args)

    def _to_adequacy_patch(self) -> Optional[AdequacyPathProperties]:
        obj = {name: getattr(self, name) for name in AdequacyPathProperties.AdequacyPathSection.model_fields}
        # If all fields are `None`, the object is empty.
        if all(value is None for value in obj.values()):
            return None
        adequacy_path_section = AdequacyPathProperties.AdequacyPathSection(**obj)
        return AdequacyPathProperties.model_validate({"adequacy_patch": adequacy_path_section})

    @property
    def area_folder(self) -> AreaFolder:
        area_folder = AreaFolder(
            optimization=self._to_optimization(),
            adequacy_patch=self._to_adequacy_patch(),
            # UI properties are not configurable in Table Mode
        )
        return area_folder
