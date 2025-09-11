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
from enum import Enum
from typing import Any, List, MutableMapping, Optional

from pydantic import field_validator
from pydantic.alias_generators import to_camel

from antarest.core.serde import AntaresBaseModel


class DistrictBaseFilter(Enum):
    add_all = "add-all"
    remove_all = "remove-all"


class DistrictUpdate(AntaresBaseModel):
    """
    Represents an update of a district.
    """

    class Config:
        alias_generator = to_camel
        extra = "forbid"
        populate_by_name = True

        @staticmethod
        def json_schema_extra(schema: MutableMapping[str, Any]) -> None:
            schema["example"] = DistrictUpdate(
                comments="Some comment", areas=["z1", "z2", "z3"], output=True
            ).model_dump(mode="json")

    @field_validator("areas", mode="before")
    def validate_areas(cls, areas: Any) -> Optional[List[str]]:
        if areas is None:
            return areas
        return list(set(areas))

    #: Indicates whether this district is used in the output (usually all
    #: districts are visible, but the user can decide to hide some of them).
    output: Optional[bool] = None
    #: User-defined comments.
    comments: Optional[str] = None
    #: List of areas that will be grouped in the district.
    areas: Optional[List[str]] = None
    #: Base filter for the district.
    base_filter: Optional[DistrictBaseFilter] = None


class DistrictCreation(AntaresBaseModel):
    """
    Represents a creation of a district.
    """

    class Config:
        alias_generator = to_camel
        extra = "forbid"
        populate_by_name = True

        @staticmethod
        def json_schema_extra(schema: MutableMapping[str, Any]) -> None:
            schema["example"] = DistrictCreation(
                name="My District", comments="", areas=["z1", "z2", "z3"], output=True
            ).model_dump(mode="json")

    @field_validator("areas", mode="before")
    def validate_areas(cls, areas: Any) -> Optional[List[str]]:
        if areas is None:
            return areas
        return list(set(areas))

    #: Name of the district (this name is also used as a unique identifier).
    name: str
    #: Indicates whether this district is used in the output (usually all
    #: districts are visible, but the user can decide to hide some of them).
    output: Optional[bool] = True
    #: User-defined comments.
    comments: Optional[str] = ""
    #: List of areas that will be grouped in the district.
    areas: Optional[List[str]] = []
    #: Base filter for the district.
    base_filter: Optional[DistrictBaseFilter] = None


class District(AntaresBaseModel):
    """
    District model.
    """

    class Config:
        alias_generator = to_camel
        extra = "forbid"
        populate_by_name = True

        @staticmethod
        def json_schema_extra(schema: MutableMapping[str, Any]) -> None:
            schema["example"] = District(
                id="my-cluster", name="My Cluster", comments="", areas=["z1", "z2", "z3"], output=True
            ).model_dump(mode="json")

    #: District identifier (based on the district name)
    id: str
    #: Indicates whether this district is used in the output (usually all
    #: districts are visible, but the user can decide to hide some of them).
    output: bool = True
    #: User-defined comments.
    comments: str = ""
    #: List of areas that will be grouped in the district.
    areas: List[str] = []
    #: Name of the district (this name is also used as a unique identifier).
    name: str


def create_district(district_creation: DistrictCreation, district_id: str) -> District:
    """
    Creates a district  from a creation request.
    """
    return District.model_validate(
        {
            **district_creation.model_dump(exclude_none=True, include={"name", "areas", "output", "comments"}),
            "id": district_id,
        }
    )
