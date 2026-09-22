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
from typing import Any

from pydantic import ConfigDict, Field

from antarest.core.serde import AntaresBaseModel
from antarest.core.utils.string import to_kebab_case
from antarest.study.business.model.common import CommaSeparatedFilterOptions
from antarest.study.business.model.link_model import (
    AssetType,
    Link,
    LinkStyle,
    LinkUpdate,
    TransmissionCapacity,
)


class LinkFileData(AntaresBaseModel):
    """
    Link properties for serialization in ini file.
    """

    model_config = ConfigDict(alias_generator=to_kebab_case, populate_by_name=True, extra="forbid")

    hurdles_cost: bool | None = None
    loop_flow: bool | None = None
    use_phase_shifter: bool | None = None
    transmission_capacities: TransmissionCapacity | None = None
    asset_type: AssetType | None = None
    display_comments: bool | None = None
    comments: str | None = None
    colorr: int | None = Field(default=None, ge=0, le=255)
    colorb: int | None = Field(default=None, ge=0, le=255)
    colorg: int | None = Field(default=None, ge=0, le=255)
    link_width: float | None = None
    link_style: LinkStyle | None = None
    filter_synthesis: CommaSeparatedFilterOptions | None = None
    filter_year_by_year: CommaSeparatedFilterOptions | None = None

    def to_model(self, area_from: str, area_to: str) -> Link:
        data = self.model_dump(exclude_none=True) | {"area1": area_from, "area2": area_to}
        return Link(**data)

    @classmethod
    def from_model(cls, link: Link) -> "LinkFileData":
        return cls.model_validate(link.model_dump(exclude={"area1", "area2"}))

    def to_update_model(self) -> LinkUpdate:
        return LinkUpdate.model_validate(self.model_dump(mode="json", exclude_none=True))


def parse_link(data: dict[str, Any], area_from: str, area_to: str) -> Link:
    return LinkFileData.model_validate(data).to_model(area_from, area_to)


def parse_link_for_update(data: dict[str, Any]) -> LinkUpdate:
    return LinkFileData.model_validate(data).to_update_model()


def serialize_link(link: Link) -> dict[str, Any]:
    return LinkFileData.from_model(link).model_dump(by_alias=True, exclude_none=True)
