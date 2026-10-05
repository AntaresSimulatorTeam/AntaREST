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
from collections.abc import MutableMapping
from enum import Enum
from typing import Any

from antares.study.version import StudyVersion
from pydantic import ConfigDict, Field, field_validator
from pydantic.alias_generators import to_camel

from antarest.core.serde import AntaresBaseModel
from antarest.study.business.model.common import FILTER_VALUES, CommaSeparatedFilterOptions
from antarest.study.business.model.utils import check_min_version, initialize_field_with_default_value
from antarest.study.model import STUDY_VERSION_10_2


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
    def validate_areas(cls, areas: Any) -> list[str] | None:
        if areas is None:
            return areas
        return list(set(areas))

    #: Indicates whether this district is used in the output (usually all
    #: districts are visible, but the user can decide to hide some of them).
    output: bool | None = None
    #: User-defined comments.
    comments: str | None = None
    #: List of areas that will be grouped in the district.
    #: This field take two meaning depending on the content of apply_filter.
    #: When apply filter is "add_all" this command means "we want all areas except those in this list". This list will be stored in District.subtract_areas
    #: Otherwise, this command means "we want no areas except those in this list". This list will be stored in District.add_areas
    areas: list[str] | None = None
    #: Base filter for the district.
    apply_filter: DistrictApplyFilter | None = None
    # Since v10.2
    filter_synthesis: CommaSeparatedFilterOptions | None = Field(default=None)
    filter_year_by_year: CommaSeparatedFilterOptions | None = Field(default=None)


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
    def validate_areas(cls, areas: Any) -> list[str] | None:
        if areas is None:
            return areas
        return list(set(areas))

    #: Name of the district (this name is also used as a unique identifier).
    name: str
    #: Indicates whether this district is used in the output (usually all
    #: districts are visible, but the user can decide to hide some of them).
    output: bool | None = None
    #: User-defined comments.
    comments: str | None = None
    #: List of areas that will be grouped in the district.
    #: This field take two meaning depending on the content of apply_filter.
    #: When apply filter is "add_all" this command means "we want all areas except those in this list". This list will be stored in District.subtract_areas
    #: Otherwise, this command means "we want no areas except those in this list". This list will be stored in District.add_areas
    areas: list[str] | None = None
    #: Base filter for the district.
    apply_filter: DistrictApplyFilter | None = None
    # Since v10.2
    filter_synthesis: CommaSeparatedFilterOptions | None = Field(default=None)
    filter_year_by_year: CommaSeparatedFilterOptions | None = Field(default=None)


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
    areas: list[str]
    #: Name of the district (this name is also used as a unique identifier).
    name: str
    # Since v10.2
    filter_synthesis: CommaSeparatedFilterOptions | None = Field(default=None)
    filter_year_by_year: CommaSeparatedFilterOptions | None = Field(default=None)


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
    add_areas: list[str] = []
    #: List of areas that will be grouped in the district.
    subtract_areas: list[str] = []
    #: Name of the district (this name is also used as a unique identifier).
    name: str
    #: Base filter for the district.
    apply_filter: DistrictApplyFilter = DistrictApplyFilter.remove_all
    # Since v10.2
    filter_synthesis: CommaSeparatedFilterOptions | None = Field(default=None)
    filter_year_by_year: CommaSeparatedFilterOptions | None = Field(default=None)

    def to_dto(self, all_areas: list[str]) -> DistrictDTO:
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
                "filter_synthesis": self.filter_synthesis,
                "filter_year_by_year": self.filter_year_by_year,
            }
        )


def initialize_district(district: District, version: StudyVersion) -> None:
    """
    Set undefined version-specific fields to default values.
    """
    if version >= STUDY_VERSION_10_2:
        for field in ["filter_synthesis", "filter_year_by_year"]:
            initialize_field_with_default_value(district, field, FILTER_VALUES)


def validate_district_against_version(version: StudyVersion, district: District) -> None:
    """
    Validates input district data against the provided study versions

    Will raise an InvalidFieldForVersionError if a field is not valid for the given study version.
    """
    if version < STUDY_VERSION_10_2:
        for field in ["filter_synthesis", "filter_year_by_year"]:
            check_min_version(district, field, version)


def create_district(district_creation: DistrictCreation, district_id: str, version: StudyVersion) -> District:
    """
    Creates a district  from a creation request.
    """
    apply_filter = district_creation.apply_filter or DistrictApplyFilter.remove_all
    add_areas = district_creation.areas if apply_filter == DistrictApplyFilter.remove_all else []
    subtract_areas = district_creation.areas if apply_filter == DistrictApplyFilter.add_all else []
    fields_to_include = {"name", "output", "comments", "filter_synthesis", "filter_year_by_year"}
    district = District.model_validate(
        {
            **district_creation.model_dump(exclude_none=True, include=fields_to_include),
            "add_areas": add_areas or [],
            "subtract_areas": subtract_areas or [],
            "apply_filter": apply_filter,
            "id": district_id,
        }
    )
    validate_district_against_version(version, district)
    initialize_district(district, version)
    return district


def update_district(district: District, district_update: DistrictUpdate) -> District:
    # Merge existing district data with the update parameters
    updated_district = District.model_validate(
        {
            **district.model_dump(exclude_none=True),
            **district_update.model_dump(
                mode="json",
                exclude_none=True,
                include={"output", "comments", "apply_filter", "filter_synthesis", "filter_year_by_year"},
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


def check_district_complete(district: District, version: StudyVersion) -> None:
    """
    Raise ValueError if any version-required field on `district` is None.
    """
    if version >= STUDY_VERSION_10_2:
        required = ["filter_synthesis", "filter_year_by_year"]
        missing = [f for f in required if getattr(district, f) is None]
        if missing:
            raise ValueError(f"District '{district.id}' is missing required field(s) for version {version}: {missing}")
