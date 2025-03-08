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
from typing import Set, Dict, Any, List, Iterable

from pydantic import model_validator, Field

from antarest.core.serde import AntaresBaseModel
from antarest.core.utils.string import to_camel_case
from antarest.study.business.all_optional_meta import all_optional_model, camel_case_model
from antarest.study.storage.rawstudy.model.filesystem.config.area import AdequacyPatchMode


FILTER_OPTIONS = ["hourly", "daily", "weekly", "monthly", "annual"]


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
    filter_synthesis: Set[str] = set(FILTER_OPTIONS)
    filter_by_year: Set[str] = set(FILTER_OPTIONS)
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
@camel_case_model
class AreaPropertiesUpdate(AntaresBaseModel, extra="forbid", populate_by_name=True):
    energy_cost_unsupplied: float
    energy_cost_spilled: float
    non_dispatch_power: bool
    dispatch_hydro_power: bool
    other_dispatch_power: bool
    spread_unsupplied_energy_cost: float
    spread_spilled_energy_cost: float
    filter_synthesis: Set[str]
    filter_by_year: Set[str]
    adequacy_patch_mode: AdequacyPatchMode

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
class AreaPropertiesProperties(AntaresBaseModel, extra="forbid", populate_by_name=True):
    energy_cost_unsupplied: Dict[str, float] = Field(alias="unserverdenergycost")
    energy_cost_spilled: Dict[str, float] = Field(alias="spilledenergycost")
    non_dispatch_power: bool = Field(alias="non-dispatchable-power")
    dispatch_hydro_power: bool = Field(alias="dispatchable-hydro-power")
    other_dispatch_power: bool = Field(alias="other-dispatchable-power")
    spread_unsupplied_energy_cost: float = Field(alias="spread-unsupplied-energy-cost")
    spread_spilled_energy_cost: float = Field(alias="spread-spilled-energy-cost")
    filter_synthesis: str = Field(alias="filter-synthesis")
    filter_by_year: str = Field(alias="filter-year-by-year")
    adequacy_patch_mode: AdequacyPatchMode = Field(alias="adequacy-patch-mode")

    def get_area_properties(self, area_id: str) -> AreaProperties:
        return AreaProperties(
            energy_cost_unsupplied=self.energy_cost_unsupplied.get(area_id, 0.0),
            energy_cost_spilled=self.energy_cost_spilled.get(area_id, 0.0),
            filter_synthesis=encode_filter(self.filter_synthesis),
            filter_by_year=encode_filter(self.filter_by_year),
            **self.model_dump(exclude={"energy_cost_unsupplied", "energy_cost_spilled", "filter_synthesis", "filter_by_year"}),
        )

    def set_area_properties(self, area_id: str, properties: AreaProperties) -> None:
        pass