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

from pydantic import Field, field_validator, model_validator
from typing_extensions import override

from antarest.study.business.enum_ignore_case import EnumIgnoreCase
from antarest.study.storage.rawstudy.model.filesystem.config.ini_properties import IniProperties
from antarest.study.storage.rawstudy.model.filesystem.config.validation import (
    validate_color_rgb,
    validate_colors,
    validate_filtering,
)


# noinspection SpellCheckingInspection
class OptimizationProperties(IniProperties):
    """
    Object linked to `/input/areas/<area>/optimization.ini` information.

    Usage:

    >>> from antarest.study.storage.rawstudy.model.filesystem.config.area import OptimizationProperties
    >>> from pprint import pprint

    Create and validate a new Optimization object from a dictionary read from a configuration file.

    >>> obj = {
    ...     "filtering": {
    ...         "filter-synthesis": "hourly, daily, weekly, monthly, annual",
    ...         "filter-year-by-year": "annual,hourly",
    ...     },
    ...     "nodal optimization": {
    ...         "non-dispatchable-power": "true",
    ...         "dispatchable-hydro-power": "false",
    ...         "spread-unsupplied-energy-cost": "1500",
    ...         "spread-spilled-energy-cost": "317.2500",
    ...     },
    ... }

    >>> opt = OptimizationProperties(**obj)

    >>> pprint(opt.model_dump(by_alias=True), width=80)
    {'filtering': {'filter-synthesis': 'hourly, daily, weekly, monthly, annual',
                   'filter-year-by-year': 'hourly, annual'},
     'nodal optimization': {'dispatchable-hydro-power': False,
                            'non-dispatchable-power': True,
                            'other-dispatchable-power': True,
                            'spread-spilled-energy-cost': 317.25,
                            'spread-unsupplied-energy-cost': 1500.0}}

    Update the filtering configuration :

    >>> opt.filtering.filter_synthesis = "hourly,weekly,monthly,annual,century"
    >>> opt.filtering.filter_year_by_year = "hourly, monthly, annual"

    Update the modal optimization configuration :

    >>> opt.nodal_optimization.non_dispatchable_power = False
    >>> opt.nodal_optimization.spread_spilled_energy_cost = 0.0

    Convert the object to a dictionary for writing to a configuration file:

    >>> pprint(opt.model_dump(by_alias=True, exclude_defaults=True), width=80)
    {'filtering': {'filter-synthesis': 'hourly, weekly, monthly, annual',
                   'filter-year-by-year': 'hourly, monthly, annual'},
     'nodal optimization': {'dispatchable-hydro-power': False,
                            'non-dispatchable-power': False,
                            'spread-unsupplied-energy-cost': 1500.0}}
    """

    class FilteringSection(IniProperties):
        """Configuration read from section `[filtering]` of `/input/areas/<area>/optimization.ini`."""

        filter_synthesis: str = Field("", alias="filter-synthesis")
        filter_year_by_year: str = Field("", alias="filter-year-by-year")

        @field_validator("filter_synthesis", "filter_year_by_year", mode="before")
        def _validate_filtering(cls, v: Any) -> str:
            return validate_filtering(v)

    # noinspection SpellCheckingInspection
    class ModalOptimizationSection(IniProperties):
        """Configuration read from section `[nodal optimization]` of `/input/areas/<area>/optimization.ini`."""

        non_dispatchable_power: bool = Field(default=True, alias="non-dispatchable-power")
        dispatchable_hydro_power: bool = Field(default=True, alias="dispatchable-hydro-power")
        other_dispatchable_power: bool = Field(default=True, alias="other-dispatchable-power")
        spread_unsupplied_energy_cost: float = Field(default=0.0, ge=0, alias="spread-unsupplied-energy-cost")
        spread_spilled_energy_cost: float = Field(default=0.0, ge=0, alias="spread-spilled-energy-cost")

    filtering: FilteringSection = Field(
        default_factory=FilteringSection,
        alias="filtering",
    )
    nodal_optimization: ModalOptimizationSection = Field(
        default_factory=ModalOptimizationSection,
        alias="nodal optimization",
    )


class AdequacyPatchMode(EnumIgnoreCase):
    """
    Adequacy patch mode.

    Only available if study version >= 830.
    """

    OUTSIDE = "outside"
    INSIDE = "inside"
    VIRTUAL = "virtual"


class AdequacyPathProperties(IniProperties):
    """
    Object linked to `/input/areas/<area>/adequacy_patch.ini` information.

    Only available if study version >= 830.
    """

    class AdequacyPathSection(IniProperties):
        """Configuration read from section `[adequacy-patch]` of `/input/areas/<area>/adequacy_patch.ini`."""

        adequacy_patch_mode: AdequacyPatchMode = Field(default=AdequacyPatchMode.OUTSIDE, alias="adequacy-patch-mode")

    adequacy_patch: AdequacyPathSection = Field(default_factory=AdequacyPathSection, alias="adequacy-patch")


class AreaUI(IniProperties):
    """
    Style of an area in the map or in a layer.

    Usage:

    >>> from antarest.study.storage.rawstudy.model.filesystem.config.area import AreaUI
    >>> from pprint import pprint

    Create and validate a new AreaUI object from a dictionary read from a configuration file.

    >>> obj = {
    ...     "x": 1148,
    ...     "y": 144,
    ...     "color_r": 0,
    ...     "color_g": 128,
    ...     "color_b": 255,
    ... }
    >>> ui = AreaUI(**obj)
    >>> pprint(ui.model_dump(by_alias=True), width=80)
    {'colorRgb': '#0080FF', 'x': 1148, 'y': 144}

    Update the color:

    >>> ui.color_rgb = (192, 168, 127)
    >>> pprint(ui.model_dump(by_alias=True), width=80)
    {'colorRgb': '#C0A87F', 'x': 1148, 'y': 144}
    """

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
        """
        Convert the object to a dictionary for writing to a configuration file:

        Usage:

        >>> from antarest.study.storage.rawstudy.model.filesystem.config.area import AreaUI
        >>> from pprint import pprint

        >>> ui = AreaUI(x=1148, y=144, color_rgb="#0080FF")
        >>> pprint(ui.to_config(), width=80)
        {'color_b': 255, 'color_g': 128, 'color_r': 0, 'x': 1148, 'y': 144}
        """
        assert self.color_rgb is not None
        r = int(self.color_rgb[1:3], 16)
        g = int(self.color_rgb[3:5], 16)
        b = int(self.color_rgb[5:7], 16)
        return {"x": self.x, "y": self.y, "color_r": r, "color_g": g, "color_b": b}


class UIProperties(IniProperties):
    """
    Object linked to `/input/areas/<area>/ui.ini` information.

    Usage:

    >>> from antarest.study.storage.rawstudy.model.filesystem.config.area import UIProperties
    >>> from pprint import pprint

    UIProperties has default values for `style` and `layers`:

    >>> ui = UIProperties()
    >>> pprint(ui.model_dump(), width=80)
    {'layer_styles': {0: {'color_rgb': '#E66C2C', 'x': 0, 'y': 0}},
     'layers': {0},
     'style': {'color_rgb': '#E66C2C', 'x': 0, 'y': 0}}

    Create and validate a new UI object from a dictionary read from a configuration file.

    >>> obj = {
    ...     "ui": {
    ...         "x": 1148,
    ...         "y": 144,
    ...         "color_r": 0,
    ...         "color_g": 128,
    ...         "color_b": 255,
    ...         "layers": "0 7",
    ...     },
    ...     "layerX": {"0": 1148, "7": 18},
    ...     "layerY": {"0": 144, "7": -22},
    ...     "layerColor": {
    ...         "0": "0 , 128 , 255",
    ...         "4": "0 , 128 , 255",
    ...         "6": "192 , 168 , 99",
    ...         "7": "0 , 128 , 255",
    ...         "8": "0 , 128 , 255",
    ...     },
    ... }

    >>> ui = UIProperties(**obj)
    >>> pprint(ui.model_dump(), width=80)
    {'layer_styles': {0: {'color_rgb': '#0080FF', 'x': 1148, 'y': 144},
                      4: {'color_rgb': '#0080FF', 'x': 1148, 'y': 144},
                      6: {'color_rgb': '#C0A863', 'x': 1148, 'y': 144},
                      7: {'color_rgb': '#0080FF', 'x': 18, 'y': -22},
                      8: {'color_rgb': '#0080FF', 'x': 1148, 'y': 144}},
     'layers': {0, 7},
     'style': {'color_rgb': '#0080FF', 'x': 1148, 'y': 144}}

    """

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
        """
        Convert the object to a dictionary for writing to a configuration file:

        Usage:

        >>> from antarest.study.storage.rawstudy.model.filesystem.config.area import UIProperties
        >>> from pprint import pprint

        >>> ui = UIProperties(
        ...     style=AreaUI(x=1148, y=144, color_rgb=(0, 128, 255)),
        ...     layers={0, 7},
        ...     layer_styles={
        ...         6: AreaUI(x=1148, y=144, color_rgb="#C0A863"),
        ...         7: AreaUI(x=18, y=-22, color_rgb=(0, 128, 255)),
        ...     },
        ... )
        >>> pprint(ui.to_config(), width=80)
        {'layerColor': {'0': '230, 108, 44', '6': '192, 168, 99', '7': '0, 128, 255'},
         'layerX': {'0': 0, '6': 1148, '7': 18},
         'layerY': {'0': 0, '6': 144, '7': -22},
         'ui': {'color_b': 255,
                'color_g': 128,
                'color_r': 0,
                'layers': '0 7',
                'x': 1148,
                'y': 144}}
        """
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


class AreaFolder(IniProperties):
    """
    Object linked to `/input/areas/<area>` information.

    Usage:

    >>> from antarest.study.storage.rawstudy.model.filesystem.config.area import AreaFolder
    >>> from pprint import pprint

    Create and validate a new AreaProperties object from a dictionary read from a configuration file.

    >>> obj = AreaFolder()
    >>> pprint(obj.model_dump(), width=80)
    {'adequacy_patch': None,
     'optimization': {'filtering': {'filter_synthesis': '',
                                    'filter_year_by_year': ''},
                      'nodal_optimization': {'dispatchable_hydro_power': True,
                                             'non_dispatchable_power': True,
                                             'other_dispatchable_power': True,
                                             'spread_spilled_energy_cost': 0.0,
                                             'spread_unsupplied_energy_cost': 0.0}},
     'ui': {'layer_styles': {0: {'color_rgb': '#E66C2C', 'x': 0, 'y': 0}},
            'layers': {0},
            'style': {'color_rgb': '#E66C2C', 'x': 0, 'y': 0}}}

    >>> pprint(obj.to_config(), width=80)
    {'optimization': {'filtering': {'filter-synthesis': '',
                                    'filter-year-by-year': ''},
                      'nodal optimization': {'dispatchable-hydro-power': True,
                                             'non-dispatchable-power': True,
                                             'other-dispatchable-power': True,
                                             'spread-spilled-energy-cost': 0.0,
                                             'spread-unsupplied-energy-cost': 0.0}},
     'ui': {'layerColor': {'0': '230, 108, 44'},
            'layerX': {'0': 0},
            'layerY': {'0': 0},
            'ui': {'color_b': 44,
                   'color_g': 108,
                   'color_r': 230,
                   'layers': '0',
                   'x': 0,
                   'y': 0}}}

    We can construct an AreaProperties object from invalid data:

    >>> data = {
    ...     "optimization": {
    ...         "filtering": {"filter-synthesis": "annual, centennial"},
    ...         "nodal optimization": {
    ...             "spread-spilled-energy-cost": "15.5",
    ...             "spread-unsupplied-energy-cost": "yes",
    ...         },
    ...     },
    ...     "ui": {"style": {"color_rgb": (0, 128, 256)}},
    ... }

    >>> obj = AreaFolder.construct(**data)
    >>> pprint(obj.model_dump(), width=80)
    {'adequacy_patch': None,
     'optimization': {'filtering': {'filter-synthesis': 'annual, centennial'},
                      'nodal optimization': {'spread-spilled-energy-cost': '15.5',
                                             'spread-unsupplied-energy-cost': 'yes'}},
     'ui': {'style': {'color_rgb': (0, 128, 256)}}}

    >>> AreaFolder.validate(data)
    Traceback (most recent call last):
      ...
    pydantic.error_wrappers.ValidationError: 1 validation error for AreaFolder
    optimization -> nodal optimization -> spread-unsupplied-energy-cost
      value is not a valid float (type=type_error.float)
    """

    optimization: OptimizationProperties = Field(
        default_factory=OptimizationProperties,
        description="optimization configuration",
    )
    adequacy_patch: Optional[AdequacyPathProperties] = Field(
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
