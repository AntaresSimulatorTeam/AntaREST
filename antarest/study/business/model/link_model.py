# Copyright (c) 2024, RTE (https://www.rte-france.com)
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

from antares.study.version import StudyVersion
from pydantic import ConfigDict, Field, model_validator

from antarest.core.exceptions import LinkValidationError
from antarest.core.serialization import AntaresBaseModel
from antarest.core.utils.string import to_camel_case, to_kebab_case
from antarest.study.model import STUDY_VERSION_8_2
from antarest.study.storage.rawstudy.model.filesystem.config.links import (
    AssetType,
    FilterOption,
    LinkStyle,
    TransmissionCapacity,
    comma_separated_enum_list,
)

DEFAULT_COLOR = 112
FILTER_VALUES: t.List[FilterOption] = [
    FilterOption.HOURLY,
    FilterOption.DAILY,
    FilterOption.WEEKLY,
    FilterOption.MONTHLY,
    FilterOption.ANNUAL,
]


class Area(AntaresBaseModel):
    area1: str
    area2: str

    @model_validator(mode="after")
    def validate_areas(self) -> t.Self:
        if self.area1 == self.area2:
            raise LinkValidationError(f"Area 1 and Area 2 can not be the same")
        return self


class LinkDTO(Area):
    model_config = ConfigDict(alias_generator=to_camel_case, populate_by_name=True, extra="forbid")

    hurdles_cost: bool = False
    loop_flow: bool = False
    use_phase_shifter: bool = False
    transmission_capacities: TransmissionCapacity = TransmissionCapacity.ENABLED
    asset_type: AssetType = AssetType.AC
    display_comments: bool = True
    colorr: int = Field(default=DEFAULT_COLOR, gt=0, lt=255)
    colorb: int = Field(default=DEFAULT_COLOR, gt=0, lt=255)
    colorg: int = Field(default=DEFAULT_COLOR, gt=0, lt=255)
    link_width: float = 1
    link_style: LinkStyle = LinkStyle.PLAIN

    filter_synthesis: t.Optional[comma_separated_enum_list] = FILTER_VALUES
    filter_year_by_year: t.Optional[comma_separated_enum_list] = FILTER_VALUES

    def to_internal(self, version: StudyVersion) -> "LinkInternal":
        if version < STUDY_VERSION_8_2 and (
            "filter_synthesis" in self.model_fields_set or "filter_year_by_year" in self.model_fields_set
        ):
            raise LinkValidationError("Cannot specify a filter value for study's version earlier than v8.2")

        return LinkInternal(
            area1=self.area1,
            area2=self.area2,
            hurdles_cost=self.hurdles_cost,
            loop_flow=self.loop_flow,
            use_phase_shifter=self.use_phase_shifter,
            transmission_capacities=self.transmission_capacities,
            asset_type=self.asset_type,
            display_comments=self.display_comments,
            colorr=self.colorr,
            colorb=self.colorb,
            colorg=self.colorg,
            link_width=self.link_width,
            link_style=self.link_style,
            filter_synthesis=self.filter_synthesis if version >= STUDY_VERSION_8_2 else None,
            filter_year_by_year=self.filter_year_by_year if version >= STUDY_VERSION_8_2 else None,
        )


class LinkInternal(AntaresBaseModel):
    model_config = ConfigDict(alias_generator=to_kebab_case, populate_by_name=True, extra="forbid")

    area1: str = "area1"
    area2: str = "area2"
    hurdles_cost: bool = False
    loop_flow: bool = False
    use_phase_shifter: bool = False
    transmission_capacities: TransmissionCapacity = TransmissionCapacity.ENABLED
    asset_type: AssetType = AssetType.AC
    display_comments: bool = True
    colorr: int = Field(default=DEFAULT_COLOR, gt=0, lt=255)
    colorb: int = Field(default=DEFAULT_COLOR, gt=0, lt=255)
    colorg: int = Field(default=DEFAULT_COLOR, gt=0, lt=255)
    link_width: float = 1
    link_style: LinkStyle = LinkStyle.PLAIN
    filter_synthesis: t.Optional[comma_separated_enum_list] = FILTER_VALUES
    filter_year_by_year: t.Optional[comma_separated_enum_list] = FILTER_VALUES

    def to_dto(self) -> LinkDTO:
        return LinkDTO(
            area1=self.area1,
            area2=self.area2,
            hurdles_cost=self.hurdles_cost,
            loop_flow=self.loop_flow,
            use_phase_shifter=self.use_phase_shifter,
            transmission_capacities=self.transmission_capacities,
            asset_type=self.asset_type,
            display_comments=self.display_comments,
            colorr=self.colorr,
            colorb=self.colorb,
            colorg=self.colorg,
            link_width=self.link_width,
            link_style=self.link_style,
            filter_synthesis=self.filter_synthesis,
            filter_year_by_year=self.filter_year_by_year,
        )
