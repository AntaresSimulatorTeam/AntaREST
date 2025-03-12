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
import re
from typing import Any, Dict, Iterable, List, Set

from pydantic import AliasChoices, Field, model_validator

from antarest.core.serde import AntaresBaseModel
from antarest.core.utils.string import to_camel_case
from antarest.study.business.all_optional_meta import all_optional_model
from antarest.study.storage.rawstudy.model.filesystem.config.area import (
    AdequacyPatchMode,
    AdequacyPathProperties,
    OptimizationProperties,
    ThermalAreasProperties,
)

FILTER_OPTIONS = ["hourly", "daily", "weekly", "monthly", "annual"]


def get_thermal_path() -> List[str]:
    return ["input", "thermal", "areas"]


def get_optimization_path(area_id: str) -> List[str]:
    return ["input", "areas", area_id, "optimization"]


def get_adequacy_patch_path(area_id: str) -> List[str]:
    return ["input", "areas", area_id, "adequacy_patch"]


def sort_filter_options(options: Iterable[str]) -> List[str]:
    return sorted(
        options,
        key=lambda x: FILTER_OPTIONS.index(x),
    )


def encode_filter(value: str) -> Set[str]:
    stripped = value.replace(" ", "")
    return set(re.split(r",", stripped) if stripped else [])


def decode_filter(encoded_value: Set[str]) -> str:
    if isinstance(encoded_value, str):
        return encoded_value
    return ", ".join(sort_filter_options(encoded_value))


class AreaProperties(AntaresBaseModel, extra="forbid", populate_by_name=True, alias_generator=to_camel_case):
    energy_cost_unsupplied: float = 0.0
    energy_cost_spilled: float = 0.0
    non_dispatch_power: bool = True
    dispatch_hydro_power: bool = True
    other_dispatch_power: bool = True
    spread_unsupplied_energy_cost: float = 0.0
    spread_spilled_energy_cost: float = 0.0
    filter_synthesis: Set[str] = Field(default_factory=lambda: set(FILTER_OPTIONS))
    filter_by_year: Set[str] = Field(default_factory=lambda: set(FILTER_OPTIONS))
    # version 830
    adequacy_patch_mode: AdequacyPatchMode = AdequacyPatchMode.OUTSIDE

    @model_validator(mode="before")
    def validation(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        filters = {
            "filter_synthesis": values.get("filter_synthesis"),
            "filter_by_year": values.get("filter_by_year"),
        }
        for filter_name, val in filters.items():
            if val is not None:
                options = encode_filter(decode_filter(val))
                if any(opt not in FILTER_OPTIONS for opt in options):
                    raise ValueError(f"Invalid value in '{filter_name}'")
        return values


@all_optional_model
class AreaPropertiesUpdate(AntaresBaseModel, extra="forbid", populate_by_name=True):
    """
    AreaPropertiesUpdate is a model used to update properties for areas in the
    "properties" tab and the "table mode" tab of the interface.

    The usage of `AliasChoices` enables the model to manage different alias names
    for the same property, allowing compatibility between multiple representations
    in the user interface and ensuring that updates remain consistent across both
    tabs.
    """

    energy_cost_unsupplied: float = Field(
        validation_alias=AliasChoices("averageUnsuppliedEnergyCost", "energyCostUnsupplied")
    )
    energy_cost_spilled: float = Field(validation_alias=AliasChoices("averageSpilledEnergyCost", "energyCostSpilled"))
    non_dispatch_power: bool = Field(validation_alias=AliasChoices("nonDispatchablePower", "nonDispatchPower"))
    dispatch_hydro_power: bool = Field(validation_alias=AliasChoices("dispatchableHydroPower", "dispatchHydroPower"))
    other_dispatch_power: bool = Field(validation_alias=AliasChoices("otherDispatchablePower", "otherDispatchPower"))
    spread_unsupplied_energy_cost: float = Field(alias="spreadUnsuppliedEnergyCost")
    spread_spilled_energy_cost: float = Field(alias="spreadSpilledEnergyCost")
    filter_synthesis: Set[str] = Field(alias="filterSynthesis")
    filter_by_year: Set[str] = Field(validation_alias=AliasChoices("filterYearByYear", "filterByYear"))
    adequacy_patch_mode: AdequacyPatchMode = Field(alias="adequacyPatchMode")

    @model_validator(mode="before")
    def validation(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        filters = {
            "filterSynthesis": values.get("filterSynthesis"),
            "filterYearByYear": values.get("filterYearByYear"),
        }
        for filter_name, val in filters.items():
            if val is not None:
                options = encode_filter(decode_filter(val))
                if any(opt not in FILTER_OPTIONS for opt in options):
                    raise ValueError(f"Invalid value in '{filter_name}'")
                if isinstance(val, str):
                    values[filter_name] = encode_filter(val)
        return values


@all_optional_model
class AreaPropertiesProperties(AntaresBaseModel, extra="forbid", populate_by_name=True):
    thermal_properties: ThermalAreasProperties
    optimization_properties: OptimizationProperties
    adequacy_properties: AdequacyPathProperties

    def get_area_properties(self, area_id: str) -> AreaProperties:
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
            adequacy_patch_mode=self.adequacy_properties.adequacy_patch.adequacy_patch_mode,
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
        self.adequacy_properties.adequacy_patch.adequacy_patch_mode = properties.adequacy_patch_mode
