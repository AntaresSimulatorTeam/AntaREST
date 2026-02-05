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
from enum import Enum
from typing import Any, List, MutableMapping, Optional

from pydantic import ConfigDict, field_validator
from pydantic.alias_generators import to_camel

from antarest.core.serde import AntaresBaseModel


class DistrictApplyFilter(Enum):
    add_all = "add-all"
    remove_all = "remove-all"


def _district_update_json_schema_extra(schema: MutableMapping[str, Any]) -> None:
    schema["example"] = DistrictUpdate(comments="Some comment", areas=["z1", "z2", "z3"], output=True).model_dump(
        mode="json"
    )


class DistrictUpdate(AntaresBaseModel):
    """
    Represents an update of a district.
    """

    model_config = ConfigDict(
        alias_generator=to_camel,
        extra="forbid",
        populate_by_name=True,
        json_schema_extra=_district_update_json_schema_extra,
    )

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
    #: This field take two meaning depending on the content of apply_filter.
    #: When apply filter is "add_all" this command means "we want all areas except those in this list". This list will be stored in District.subtract_areas
    #: Otherwise, this command means "we want no areas except those in this list". This list will be stored in District.add_areas
    areas: Optional[List[str]] = None
    #: Base filter for the district.
    apply_filter: Optional[DistrictApplyFilter] = None


def _district_creation_json_schema_extra(schema: MutableMapping[str, Any]) -> None:
    schema["example"] = DistrictCreation(
        name="My District", comments="", areas=["z1", "z2", "z3"], output=True
    ).model_dump(mode="json")


class DistrictCreation(AntaresBaseModel):
    """
    Represents a creation of a district.
    """

    model_config = ConfigDict(
        alias_generator=to_camel,
        extra="forbid",
        populate_by_name=True,
        json_schema_extra=_district_creation_json_schema_extra,
    )

    @field_validator("areas", mode="before")
    def validate_areas(cls, areas: Any) -> Optional[List[str]]:
        if areas is None:
            return areas
        return list(set(areas))

    #: Name of the district (this name is also used as a unique identifier).
    name: str
    #: Indicates whether this district is used in the output (usually all
    #: districts are visible, but the user can decide to hide some of them).
    output: Optional[bool] = None
    #: User-defined comments.
    comments: Optional[str] = None
    #: List of areas that will be grouped in the district.
    #: This field take two meaning depending on the content of apply_filter.
    #: When apply filter is "add_all" this command means "we want all areas except those in this list". This list will be stored in District.subtract_areas
    #: Otherwise, this command means "we want no areas except those in this list". This list will be stored in District.add_areas
    areas: Optional[List[str]] = None
    #: Base filter for the district.
    apply_filter: Optional[DistrictApplyFilter] = None


def _district_dto_json_schema_extra(schema: MutableMapping[str, Any]) -> None:
    schema["example"] = DistrictDTO(
        id="my-cluster", name="My Cluster", comments="", areas=["z1", "z2", "z3"], output=True
    ).model_dump(mode="json")


class DistrictDTO(AntaresBaseModel):
    """
    District DTO.
    """

    model_config = ConfigDict(
        alias_generator=to_camel,
        extra="forbid",
        populate_by_name=True,
        json_schema_extra=_district_dto_json_schema_extra,
    )

    #: District identifier (based on the district name)
    id: str
    #: Indicates whether this district is used in the output (usually all
    #: districts are visible, but the user can decide to hide some of them).
    output: bool
    #: User-defined comments.
    comments: str
    #: List of areas that will be grouped in the district.
    areas: List[str]
    #: Name of the district (this name is also used as a unique identifier).
    name: str


def _district_json_schema_extra(schema: MutableMapping[str, Any]) -> None:
    schema["example"] = District(
        id="my-cluster",
        name="My Cluster",
        comments="",
        add_areas=["z1", "z2", "z3"],
        subtract_areas=[],
        output=True,
    ).model_dump(mode="json")


class District(AntaresBaseModel):
    """
    District model.
    """

    model_config = ConfigDict(
        alias_generator=to_camel, extra="forbid", populate_by_name=True, json_schema_extra=_district_json_schema_extra
    )

    #: District identifier (based on the district name)
    id: str
    #: Indicates whether this district is used in the output (usually all
    #: districts are visible, but the user can decide to hide some of them).
    output: bool = True
    #: User-defined comments.
    comments: str = ""
    #: List of areas that will be grouped in the district.
    add_areas: List[str] = []
    #: List of areas that will be grouped in the district.
    subtract_areas: List[str] = []
    #: Name of the district (this name is also used as a unique identifier).
    name: str
    #: Base filter for the district.
    apply_filter: DistrictApplyFilter = DistrictApplyFilter.remove_all

    def to_dto(self, all_areas: List[str]) -> DistrictDTO:
        if self.apply_filter == DistrictApplyFilter.add_all:
            areas = list(set(all_areas).difference(set(self.subtract_areas)))
        else:
            areas = list(set(self.add_areas))
        return DistrictDTO.model_validate(
            {
                "id": self.id,
                "name": self.name,
                "areas": sorted(areas),
                "output": self.output,
                "comments": self.comments or "",
            }
        )


def create_district(district_creation: DistrictCreation, district_id: str) -> District:
    """
    Creates a district  from a creation request.
    """
    apply_filter = district_creation.apply_filter or DistrictApplyFilter.remove_all
    add_areas = district_creation.areas if apply_filter == DistrictApplyFilter.remove_all else []
    subtract_areas = district_creation.areas if apply_filter == DistrictApplyFilter.add_all else []
    return District.model_validate(
        {
            **district_creation.model_dump(exclude_none=True, include={"name", "output", "comments"}),
            "add_areas": add_areas or [],
            "subtract_areas": subtract_areas or [],
            "apply_filter": apply_filter,
            "id": district_id,
        }
    )


def update_district(district: District, district_update: DistrictUpdate) -> District:
    # Merge existing district data with the update parameters
    updated_district = District.model_validate(
        {
            **district.model_dump(
                exclude_none=True,
                include={"output", "comments", "name", "add_areas", "subtract_areas", "apply_filter", "id"},
            ),
            **district_update.model_dump(
                mode="json", exclude_none=True, include={"output", "comments", "apply_filter"}
            ),
        }
    )

    # If areas are provided, we need to update add_areas and subtract_areas based on the apply_filter
    if district_update.areas is not None:
        updated_district.add_areas, updated_district.subtract_areas = (
            (district_update.areas, [])
            if updated_district.apply_filter == DistrictApplyFilter.remove_all
            else ([], district_update.areas)
        )

    return updated_district
