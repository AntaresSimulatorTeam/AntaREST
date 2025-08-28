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
from typing import Any, List, MutableMapping

from pydantic.alias_generators import to_camel

from antarest.core.serde import AntaresBaseModel


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

    #: Indicates whether this district is used in the output (usually all
    #: districts are visible, but the user can decide to hide some of them).
    output: bool
    #: User-defined comments.
    comments: str = ""
    #: List of areas that will be grouped in the district.
    areas: List[str]


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

    #: Name of the district (this name is also used as a unique identifier).
    name: str
    #: Indicates whether this district is used in the output (usually all
    #: districts are visible, but the user can decide to hide some of them).
    output: bool
    #: User-defined comments.
    comments: str = ""
    #: List of areas that will be grouped in the district.
    areas: List[str]


class DistrictBaseFilter(Enum):
    add_all = "add-all"
    remove_all = "remove-all"


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
    output: bool
    #: User-defined comments.
    comments: str = ""
    #: List of areas that will be grouped in the district.
    areas: List[str]
    #: Name of the district (this name is also used as a unique identifier).
    name: str
