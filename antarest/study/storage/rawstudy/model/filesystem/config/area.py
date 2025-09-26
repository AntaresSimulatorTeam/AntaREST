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

"""
Object model used to read and update area configuration.
"""

from typing import Any, Dict, Mapping, MutableMapping, Optional, Set

from antares.study.version import StudyVersion
from pydantic import ConfigDict, Field, field_validator, model_validator
from typing_extensions import override

from antarest.core.serde import AntaresBaseModel
from antarest.core.utils.string import to_kebab_case
from antarest.study.business.model.area_properties_model import (
    AdequacyPatchMode,
    AreaProperties,
    decode_filter,
    encode_filter,
)
from antarest.study.model import STUDY_VERSION_8_3
from antarest.study.storage.rawstudy.model.filesystem.config.ini_properties import IniProperties
from antarest.study.storage.rawstudy.model.filesystem.config.validation import (
    validate_filtering,
)


class AreaUI(IniProperties):
    x: int = Field(default=0, description="x coordinate of the area in the map")
    y: int = Field(default=0, description="y coordinate of the area in the map")
    color_r: int = Field(default=230, description="red component of the area color")
    color_g: int = Field(default=108, description="green component of the area color")
    color_b: int = Field(default=44, description="blue component of the area color")

    @override
    def to_config(self) -> Dict[str, Any]:
        return {"x": self.x, "y": self.y, "color_r": self.color_r, "color_g": self.color_g, "color_b": self.color_b}


class UIProperties(IniProperties):
    style: AreaUI = Field(
        default_factory=AreaUI,
        description="style of the area in the map: coordinates and color",
    )
    layers: Set[int] = Field(
        default_factory=lambda: {0},
        description="layers where the area is visible",
    )
    layer_styles: Dict[int, AreaUI] = Field(
        default_factory=dict,
        description="style of the area in each layer",
        alias="layerStyles",
    )

    @staticmethod
    def _set_default_style(values: MutableMapping[str, Any]) -> Mapping[str, Any]:
        """Defined the default style if missing."""
        style = values.get("style", None)
        if style is None:
            values["style"] = AreaUI()
        elif isinstance(style, dict):
            values["style"] = AreaUI(**style)
        else:
            values["style"] = AreaUI(**style.model_dump())
        return values

    @staticmethod
    def _set_default_layer_styles(values: MutableMapping[str, Any]) -> Mapping[str, Any]:
        """Define the default layer styles if missing."""
        layer_styles = values.get("layer_styles")
        if layer_styles is None:
            values["layer_styles"] = {0: AreaUI()}
        elif isinstance(layer_styles, dict):
            values["layer_styles"] = {0: AreaUI()}
            for key, style in layer_styles.items():
                key = int(key)
                if isinstance(style, dict):
                    values["layer_styles"][key] = AreaUI(**style)
                else:
                    values["layer_styles"][key] = AreaUI(**style.model_dump())
        else:
            raise TypeError(f"Invalid type for layer_styles: {type(layer_styles)}")
        return values

    @model_validator(mode="before")
    def _validate_layers(cls, values: MutableMapping[str, Any]) -> Mapping[str, Any]:
        cls._set_default_style(values)
        cls._set_default_layer_styles(values)
        # Parse the `[ui]` section (if any)
        ui_section = values.pop("ui", {})
        if ui_section:
            # If `layers` is a single integer, convert it to `str` first
            layers = str(ui_section.pop("layers", "0"))
            values["layers"] = set([int(layer) for layer in layers.split()])
            style = values["style"]
            style.x = ui_section.pop("x", style.x)
            style.y = ui_section.pop("y", style.y)
            style.color_r = ui_section.pop("color_r", style.color_r)
            style.color_g = ui_section.pop("color_g", style.color_g)
            style.color_b = ui_section.pop("color_b", style.color_b)

        # Parse the `[layerX]`, `[layerY]` and `[layerColor]` sections (if any)
        layer_x_section = values.pop("layerX", {})
        layer_y_section = values.pop("layerY", {})
        layer_color_section = values.pop("layerColor", {})
        # Key are converted to `int` and values to `str` (for splitting)
        layer_x_section = {int(layer): str(x) for layer, x in layer_x_section.items()}
        layer_y_section = {int(layer): str(y) for layer, y in layer_y_section.items()}
        layer_color_section = {int(layer): str(color) for layer, color in layer_color_section.items()}
        # indexes must contain all the keys from the three sections
        indexes = set(layer_x_section) | set(layer_y_section) | set(layer_color_section)
        if indexes:
            layer_styles = {index: values["style"].copy() for index in indexes}
            for layer, x in layer_x_section.items():
                layer_styles[layer].x = int(x)
            for layer, y in layer_y_section.items():
                layer_styles[layer].y = int(y)
            for layer, color in layer_color_section.items():
                r, g, b = [int(c) for c in color.split(",")]
                layer_styles[layer].color_r = r
                layer_styles[layer].color_g = g
                layer_styles[layer].color_b = b
            values["layer_styles"].update(layer_styles)
            values["layers"] = values["layers"].intersection(indexes)

        return values

    @override
    def to_config(self) -> Dict[str, Dict[str, Any]]:
        obj: Dict[str, Dict[str, Any]] = {
            "ui": {},
            "layerX": {},
            "layerY": {},
            "layerColor": {},
        }
        obj["ui"].update(self.style.to_config())
        obj["ui"]["layers"] = " ".join(str(layer) for layer in sorted(self.layers))
        for layer, style in self.layer_styles.items():
            obj["layerX"][str(layer)] = style.x
            obj["layerY"][str(layer)] = style.y
            obj["layerColor"][str(layer)] = f"{style.color_r}, {style.color_g}, {style.color_b}"
        return obj


class OptimizationFileData(AntaresBaseModel):
    model_config = ConfigDict(alias_generator=to_kebab_case, populate_by_name=True, extra="forbid")

    class FilteringSection(AntaresBaseModel):
        model_config = ConfigDict(alias_generator=to_kebab_case, populate_by_name=True, extra="forbid")

        filter_synthesis: str = Field("")
        filter_year_by_year: str = Field("")

        @field_validator("filter_synthesis", "filter_year_by_year", mode="before")
        def _validate_filtering(cls, v: Any) -> str:
            return validate_filtering(v)

    class ModalOptimizationSection(AntaresBaseModel):
        model_config = ConfigDict(alias_generator=to_kebab_case, populate_by_name=True, extra="forbid")

        non_dispatchable_power: bool = Field(default=True)
        dispatchable_hydro_power: bool = Field(default=True)
        other_dispatchable_power: bool = Field(default=True)
        spread_unsupplied_energy_cost: float = Field(default=0.0)
        spread_spilled_energy_cost: float = Field(default=0.0)

    filtering: FilteringSection = Field(
        default_factory=FilteringSection,
    )
    nodal_optimization: ModalOptimizationSection = Field(
        default_factory=ModalOptimizationSection,
        alias="nodal optimization",
    )


class AdequacyPatchFileData(AntaresBaseModel):
    """
    Only available if study version >= 830.
    """

    model_config = ConfigDict(alias_generator=to_kebab_case, populate_by_name=True, extra="forbid")

    class AdequacyPathSection(AntaresBaseModel):
        model_config = ConfigDict(alias_generator=to_kebab_case, populate_by_name=True, extra="forbid")
        adequacy_patch_mode: AdequacyPatchMode = Field(default=AdequacyPatchMode.OUTSIDE)

    adequacy_patch: AdequacyPathSection = Field(default_factory=AdequacyPathSection)


class AreaFileData(AntaresBaseModel):
    model_config = ConfigDict(alias_generator=to_kebab_case, populate_by_name=True, extra="forbid")

    optimization: OptimizationFileData = Field(
        default_factory=OptimizationFileData,
        description="optimization configuration",
    )
    adequacy_patch: Optional[AdequacyPatchFileData] = Field(
        None,
        description="adequacy patch configuration",
    )
    ui: UIProperties = Field(
        default_factory=UIProperties,
        description="UI configuration",
    )


# noinspection SpellCheckingInspection
class ThermalAreasProperties(IniProperties):
    """
    Object linked to `/input/thermal/areas.ini` information.
    """

    unserverd_energy_cost: MutableMapping[str, float] = Field(
        default_factory=dict,
        alias="unserverdenergycost",
        description="unserverd energy cost (€/MWh) of each area",
    )

    spilled_energy_cost: MutableMapping[str, float] = Field(
        default_factory=dict,
        alias="spilledenergycost",
        description="spilled energy cost (€/MWh) of each area",
    )

    @field_validator("unserverd_energy_cost", "spilled_energy_cost", mode="before")
    def _validate_energy_cost(cls, v: Any) -> MutableMapping[str, float]:
        if isinstance(v, dict):
            return {str(k): float(v) for k, v in v.items()}
        raise TypeError(f"Invalid type for energy cost: {type(v)}")


class AreaPropertiesFileData(AntaresBaseModel, extra="forbid", populate_by_name=True):
    thermal_properties: ThermalAreasProperties
    optimization_properties: OptimizationFileData
    adequacy_properties: AdequacyPatchFileData

    def get_area_properties(self, area_id: str, study_version: StudyVersion) -> AreaProperties:
        adequacy_patch_mode = (
            None if study_version < STUDY_VERSION_8_3 else self.adequacy_properties.adequacy_patch.adequacy_patch_mode
        )
        return AreaProperties(
            energy_cost_unsupplied=self.thermal_properties.unserverd_energy_cost.get(area_id, 0.0),
            energy_cost_spilled=self.thermal_properties.spilled_energy_cost.get(area_id, 0.0),
            non_dispatch_power=self.optimization_properties.nodal_optimization.non_dispatchable_power,
            dispatch_hydro_power=self.optimization_properties.nodal_optimization.dispatchable_hydro_power,
            other_dispatch_power=self.optimization_properties.nodal_optimization.other_dispatchable_power,
            spread_unsupplied_energy_cost=self.optimization_properties.nodal_optimization.spread_unsupplied_energy_cost,
            spread_spilled_energy_cost=self.optimization_properties.nodal_optimization.spread_spilled_energy_cost,
            filter_synthesis=encode_filter(self.optimization_properties.filtering.filter_synthesis),
            filter_by_year=encode_filter(self.optimization_properties.filtering.filter_year_by_year),
            adequacy_patch_mode=adequacy_patch_mode,
        )

    def set_area_properties(self, area_id: str, properties: AreaProperties) -> None:
        self.thermal_properties.unserverd_energy_cost[area_id] = properties.energy_cost_unsupplied
        self.thermal_properties.spilled_energy_cost[area_id] = properties.energy_cost_spilled
        self.optimization_properties.nodal_optimization.non_dispatchable_power = properties.non_dispatch_power
        self.optimization_properties.nodal_optimization.dispatchable_hydro_power = properties.dispatch_hydro_power
        self.optimization_properties.nodal_optimization.other_dispatchable_power = properties.other_dispatch_power
        self.optimization_properties.nodal_optimization.spread_unsupplied_energy_cost = (
            properties.spread_unsupplied_energy_cost
        )
        self.optimization_properties.nodal_optimization.spread_spilled_energy_cost = (
            properties.spread_spilled_energy_cost
        )
        self.optimization_properties.filtering.filter_synthesis = decode_filter(properties.filter_synthesis)
        self.optimization_properties.filtering.filter_year_by_year = decode_filter(properties.filter_by_year)
        if properties.adequacy_patch_mode:
            self.adequacy_properties.adequacy_patch.adequacy_patch_mode = properties.adequacy_patch_mode
