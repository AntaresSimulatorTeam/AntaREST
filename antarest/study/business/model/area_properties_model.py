# Copyright (c) 2026, RTE (https://www.rte-france.com)
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
from collections.abc import Iterable
from typing import Literal, TypeAlias, cast

from antares.study.version import StudyVersion
from pydantic import Field

from antarest.core.serde import AntaresBaseModel
from antarest.core.utils.string import to_camel_case
from antarest.study.business.enum_ignore_case import EnumIgnoreCase
from antarest.study.model import STUDY_VERSION_8_3

FrequencyFilter: TypeAlias = Literal["hourly", "daily", "weekly", "monthly", "annual"]

FILTER_OPTIONS: list[FrequencyFilter] = ["hourly", "daily", "weekly", "monthly", "annual"]


class AdequacyPatchMode(EnumIgnoreCase):
    """
    Adequacy patch mode.

    Only available if study version >= 830.
    """

    OUTSIDE = "outside"
    INSIDE = "inside"
    VIRTUAL = "virtual"


def sort_filter_options(options: Iterable[FrequencyFilter]) -> list[FrequencyFilter]:
    return sorted(
        options,
        key=lambda x: FILTER_OPTIONS.index(x),
    )


def parse_filters(value: str) -> set[FrequencyFilter]:
    if not value:
        return set()
    return {_validate_filter(item.strip()) for item in value.split(",")}


def _validate_filter(value: str) -> FrequencyFilter:
    if value not in FILTER_OPTIONS:
        raise ValueError(f"Invalid filter {value}, expected one of {','.join(FILTER_OPTIONS)}.")
    return cast(FrequencyFilter, value)


def serialize_filters(encoded_value: set[FrequencyFilter]) -> str:
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
    filter_synthesis: set[FrequencyFilter] = Field(default_factory=lambda: set(FILTER_OPTIONS))
    filter_by_year: set[FrequencyFilter] = Field(default_factory=lambda: set(FILTER_OPTIONS))

    # version 830
    adequacy_patch_mode: AdequacyPatchMode | None = None


class AreaPropertiesUpdate(AntaresBaseModel, extra="forbid", populate_by_name=True, alias_generator=to_camel_case):
    """
    AreaPropertiesUpdate is a model used to update properties for areas in the
    "properties" tab and the "table mode" tab of the interface.
    """

    energy_cost_unsupplied: float | None = None
    energy_cost_spilled: float | None = None
    non_dispatch_power: bool | None = None
    dispatch_hydro_power: bool | None = None
    other_dispatch_power: bool | None = None
    spread_unsupplied_energy_cost: float | None = None
    spread_spilled_energy_cost: float | None = None
    filter_synthesis: set[FrequencyFilter] | None = None
    filter_by_year: set[FrequencyFilter] | None = None
    adequacy_patch_mode: AdequacyPatchMode | None = None


def initialize_area_properties(area_props: AreaProperties, study_version: StudyVersion) -> None:
    if study_version >= STUDY_VERSION_8_3 and area_props.adequacy_patch_mode is None:
        area_props.adequacy_patch_mode = AdequacyPatchMode.OUTSIDE


def update_area_properties(area_properties: AreaProperties, data: AreaPropertiesUpdate) -> AreaProperties:
    current_properties = area_properties.model_dump(mode="json")
    new_properties = data.model_dump(mode="json", exclude_none=True)
    current_properties.update(new_properties)
    return AreaProperties.model_validate(current_properties)
