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

from typing import List

from antarest.core.serde import AntaresBaseModel


class DistrictUpdateDTO(AntaresBaseModel):
    #: Indicates whether this district is used in the output (usually all
    #: districts are visible, but the user can decide to hide some of them).
    output: bool
    #: User-defined comments.
    comments: str = ""
    #: List of areas that will be grouped in the district.
    areas: List[str]


class DistrictCreationDTO(DistrictUpdateDTO):
    #: Name of the district (this name is also used as a unique identifier).
    name: str


class DistrictInfoDTO(DistrictCreationDTO):
    #: District identifier (based on the district name)
    id: str


class District(AntaresBaseModel):
    """Business model representing a district."""
    id: str
    name: str
    areas: List[str]
    output: bool
    comments: str = ""