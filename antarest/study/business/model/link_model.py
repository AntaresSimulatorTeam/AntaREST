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
from typing import Optional, Self

from pydantic import ConfigDict, Field, model_validator

from antarest.core.exceptions import LinkValidationError
from antarest.core.serde import AntaresBaseModel
from antarest.core.utils.string import to_camel_case
from antarest.study.business.enum_ignore_case import EnumIgnoreCase
from antarest.study.business.model.common import FILTER_VALUES, CommaSeparatedFilterOptions
from antarest.study.storage.rawstudy.model.filesystem.config.model import LinkConfig


class AssetType(EnumIgnoreCase):
    """
    Enum representing the type of asset for a link between two areas.

    Attributes:
        AC: Represents an Alternating Current link. This is the most common type of electricity transmission.
        DC: Represents a Direct Current link. This is typically used for long-distance transmission.
        GAZ: Represents a gas link. This is used when the link is related to gas transmission.
        VIRT: Represents a virtual link. This is used when the link doesn't physically exist
            but is used for modeling purposes.
        OTHER: Represents any other type of link that doesn't fall into the above categories.
    """

    AC = "ac"
    DC = "dc"
    GAZ = "gaz"
    VIRT = "virt"
    OTHER = "other"


class TransmissionCapacity(EnumIgnoreCase):
    """
    Enum representing the transmission capacity of a link.

    Attributes:
        INFINITE: Represents a link with infinite transmission capacity.
            This means there are no limits on the amount of electricity that can be transmitted.
        IGNORE: Represents a link where the transmission capacity is ignored.
            This means the capacity is not considered during simulations.
        ENABLED: Represents a link with a specific transmission capacity.
            This means the capacity is considered in the model and has a certain limit.
    """

    INFINITE = "infinite"
    IGNORE = "ignore"
    ENABLED = "enabled"


class LinkStyle(EnumIgnoreCase):
    """
    Enum representing the style of a link in a network visualization.

    Attributes:
        DOT: Represents a dotted line style.
        PLAIN: Represents a solid line style.
        DASH: Represents a dashed line style.
        DOT_DASH: Represents a line style with alternating dots and dashes.
    """

    DOT = "dot"
    PLAIN = "plain"
    DASH = "dash"
    DOT_DASH = "dotdash"
    OTHER = "other"


DEFAULT_COLOR = 112


class LinkUpdate(AntaresBaseModel):
    model_config = ConfigDict(alias_generator=to_camel_case, populate_by_name=True, extra="forbid")

    hurdles_cost: Optional[bool] = None
    loop_flow: Optional[bool] = None
    use_phase_shifter: Optional[bool] = None
    transmission_capacities: Optional[TransmissionCapacity] = None
    asset_type: Optional[AssetType] = None
    display_comments: Optional[bool] = None
    comments: Optional[str] = None
    colorr: Optional[int] = None
    colorb: Optional[int] = None
    colorg: Optional[int] = None
    link_width: Optional[float] = None
    link_style: Optional[LinkStyle] = None
    filter_synthesis: Optional[CommaSeparatedFilterOptions] = None
    filter_year_by_year: Optional[CommaSeparatedFilterOptions] = None


class Link(AntaresBaseModel):
    model_config = ConfigDict(alias_generator=to_camel_case, populate_by_name=True, extra="forbid")

    area1: str
    area2: str
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
    filter_synthesis: CommaSeparatedFilterOptions = Field(default_factory=lambda: FILTER_VALUES)
    filter_year_by_year: CommaSeparatedFilterOptions = Field(default_factory=lambda: FILTER_VALUES)

    @model_validator(mode="after")
    def validate_areas(self) -> Self:
        if self.area1 == self.area2:
            raise LinkValidationError(f"Cannot create a link that goes from and to the same single area: {self.area1}")
        area_from, area_to = sorted([self.area1, self.area2])
        self.area1 = area_from
        self.area2 = area_to
        return self

    def to_config(self) -> LinkConfig:
        data = self.model_dump(mode="json", include={"filter_synthesis", "filter_year_by_year"})
        return LinkConfig(**data)


class LinkCreation(AntaresBaseModel):
    model_config = ConfigDict(alias_generator=to_camel_case, populate_by_name=True, extra="forbid")

    hurdles_cost: Optional[bool] = None
    loop_flow: Optional[bool] = None
    use_phase_shifter: Optional[bool] = None
    transmission_capacities: Optional[TransmissionCapacity] = None
    asset_type: Optional[AssetType] = None
    display_comments: Optional[bool] = None
    comments: Optional[str] = None
    colorr: Optional[int] = None
    colorb: Optional[int] = None
    colorg: Optional[int] = None
    link_width: Optional[float] = None
    link_style: Optional[LinkStyle] = None
    filter_synthesis: Optional[CommaSeparatedFilterOptions] = None
    filter_year_by_year: Optional[CommaSeparatedFilterOptions] = None

    @classmethod
    def from_link(cls, link: Link) -> "LinkCreation":
        """
        Conversion to creation request. Can be useful for duplicating clusters.
        """
        return LinkCreation.model_validate(link.model_dump(mode="json", exclude={"id", "area1", "area2"}))


def create_link(link_data: LinkCreation, area_from: str, area_to: str) -> Link:
    """
    Creates a link from a creation request
    """
    return Link(**{"area1": area_from, "area2": area_to, **link_data.model_dump(mode="json", exclude_none=True)})


def update_link(link: Link, data: LinkUpdate) -> Link:
    """
    Updates a link according to the provided update data.
    """
    current_properties = link.model_dump(mode="json")
    new_properties = data.model_dump(mode="json", exclude_none=True)
    current_properties.update(new_properties)
    return Link.model_validate(current_properties)
