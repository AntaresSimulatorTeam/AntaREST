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

from pydantic import ConfigDict, Field, field_validator, model_validator
from typing_extensions import override

from antarest.core.serde import AntaresBaseModel
from antarest.core.utils.string import to_kebab_case
from antarest.study.business.enum_ignore_case import EnumIgnoreCase
from antarest.study.storage.rawstudy.model.filesystem.config.ini_properties import IniProperties
from antarest.study.storage.rawstudy.model.filesystem.config.validation import (
    validate_color_rgb,
    validate_colors,
    validate_filtering,
)


class AdequacyPatchMode(EnumIgnoreCase):
    """
    Adequacy patch mode.

    Only available if study version >= 830.
    """

    OUTSIDE = "outside"
    INSIDE = "inside"
    VIRTUAL = "virtual"


class AreaUI(IniProperties):
    x: int = Field(default=0, description="x coordinate of the area in the map")
    y: int = Field(default=0, description="y coordinate of the area in the map")
    color_rgb: str = Field(
        default="#E66C2C",
        alias="colorRgb",
        description="color of the area in the map",
    )

    @field_validator("color_rgb", mode="before")
    def _validate_color_rgb(cls, v: Any) -> str:
        return validate_color_rgb(v)

    @model_validator(mode="before")
    def _validate_colors(cls, values: MutableMapping[str, Any]) -> Mapping[str, Any]:
        return validate_colors(values)

    @override
    def to_config(self) -> Dict[str, Any]:
        assert self.color_rgb is not None
        r = int(self.color_rgb[1:3], 16)
        g = int(self.color_rgb[3:5], 16)
        b = int(self.color_rgb[5:7], 16)
        return {"x": self.x, "y": self.y, "color_r": r, "color_g": g, "color_b": b}


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
            values["style"].x = ui_section.pop("x", values["style"].x)
            values["style"].y = ui_section.pop("y", values["style"].y)
            values["style"].color_rgb = (
                ui_section.pop("color_r", values["style"].color_rgb[0]),
                ui_section.pop("color_g", values["style"].color_rgb[1]),
                ui_section.pop("color_b", values["style"].color_rgb[2]),
            )

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
                layer_styles[layer].color_rgb = r, g, b
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
            assert style.color_rgb is not None
            r = int(style.color_rgb[1:3], 16)
            g = int(style.color_rgb[3:5], 16)
            b = int(style.color_rgb[5:7], 16)
            obj["layerColor"][str(layer)] = f"{r}, {g}, {b}"
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


class AdequacyPathFileData(AntaresBaseModel):
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
    adequacy_patch: Optional[AdequacyPathFileData] = Field(
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

    Usage:

    >>> from antarest.study.storage.rawstudy.model.filesystem.config.area import ThermalAreasProperties
    >>> from pprint import pprint

    Create and validate a new ThermalArea object from a dictionary read from a configuration file::

        [unserverdenergycost]
        at = 4000.80
        be = 3500
        de = 1250
        fr = 138.50

        [spilledenergycost]
        cz = 100.0

    >>> obj = {
    ...     "unserverdenergycost": {
    ...         "at": "4000.80",
    ...         "be": "3500",
    ...         "de": "1250",
    ...         "fr": "138.50",
    ...     },
    ...     "spilledenergycost": {
    ...         "cz": "100.0",
    ...     },
    ... }
    >>> area = ThermalAreasProperties(**obj)
    >>> pprint(area.model_dump(), width=80)
    {'spilled_energy_cost': {'cz': 100.0},
     'unserverd_energy_cost': {'at': 4000.8,
                               'be': 3500.0,
                               'de': 1250.0,
                               'fr': 138.5}}

    Update the unserverd energy cost:

    >>> area.unserverd_energy_cost["at"] = 6500.0
    >>> area.unserverd_energy_cost["fr"] = 0.0
    >>> pprint(area.model_dump(), width=80)
    {'spilled_energy_cost': {'cz': 100.0},
     'unserverd_energy_cost': {'at': 6500.0, 'be': 3500.0, 'de': 1250.0, 'fr': 0.0}}

    Convert the object to a dictionary for writing to a configuration file:

    >>> pprint(area.to_config(), width=80)
    {'spilledenergycost': {'cz': 100.0},
     'unserverdenergycost': {'at': 6500.0, 'be': 3500.0, 'de': 1250.0, 'fr': 0.0}}
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
