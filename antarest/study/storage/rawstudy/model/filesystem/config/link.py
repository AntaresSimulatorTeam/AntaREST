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
from typing import Any, Optional

from antares.study.version import StudyVersion
from pydantic import ConfigDict, Field

from antarest.core.serde import AntaresBaseModel
from antarest.core.utils.string import to_kebab_case
from antarest.study.business.model.link_model import (
    DEFAULT_COLOR,
    AssetType,
    CommaSeparatedFilterOptions,
    Link,
    LinkStyle,
    TransmissionCapacity,
    initialize_link,
    validate_link_against_version,
)


class LinkFileData(AntaresBaseModel):
    """
    Link properties for serialization in ini file.
    """

    model_config = ConfigDict(alias_generator=to_kebab_case, populate_by_name=True, extra="forbid")

    hurdles_cost: bool = False
    loop_flow: bool = False
    use_phase_shifter: bool = False
    transmission_capacities: TransmissionCapacity = TransmissionCapacity.ENABLED
    asset_type: AssetType = AssetType.AC
    display_comments: bool = True
    comments: str = ""
    colorr: int = Field(default=DEFAULT_COLOR, ge=0, le=255)
    colorb: int = Field(default=DEFAULT_COLOR, ge=0, le=255)
    colorg: int = Field(default=DEFAULT_COLOR, ge=0, le=255)
    link_width: float = 1
    link_style: LinkStyle = LinkStyle.PLAIN
    # v8.2 fields
    filter_synthesis: Optional[CommaSeparatedFilterOptions] = None
    filter_year_by_year: Optional[CommaSeparatedFilterOptions] = None

    def to_model(self, area_from: str, area_to: str) -> Link:
        data = self.model_dump(exclude_none=True) | {"area1": area_from, "area2": area_to}
        return Link(**data)

    @classmethod
    def from_model(cls, link: Link) -> "LinkFileData":
        return cls.model_validate(link.model_dump(exclude={"area1", "area2"}))


def parse_link(study_version: StudyVersion, data: Any, area_from: str, area_to: str) -> Link:
    link = LinkFileData.model_validate(data).to_model(area_from, area_to)
    validate_link_against_version(study_version, link)
    initialize_link(link, study_version)
    return link


def serialize_link(study_version: StudyVersion, link: Link) -> dict[str, Any]:
    validate_link_against_version(study_version, link)
    return LinkFileData.from_model(link).model_dump(by_alias=True, exclude_none=True, exclude={"area1", "area2"})
