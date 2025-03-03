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

import enum
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Union

import typing_extensions as te
from pydantic import StringConstraints

from antarest.core.serde import AntaresBaseModel

if TYPE_CHECKING:
    # These dependencies are only used for type checking with mypy.
    from antarest.study.model import Study, StudyMetadataDTO

JSON = Dict[str, Any]
ELEMENT = Union[str, int, float, bool, bytes]
SUB_JSON = Union[ELEMENT, JSON, List[Any], None]
LowerCaseStr = te.Annotated[str, StringConstraints(to_lower=True)]


class PublicMode(enum.StrEnum):
    NONE = "NONE"
    READ = "READ"
    EXECUTE = "EXECUTE"
    EDIT = "EDIT"
    FULL = "FULL"


class StudyPermissionType(enum.StrEnum):
    """
    User permission belongs to Study
    """

    READ = "READ"
    RUN = "RUN"
    WRITE = "WRITE"
    MANAGE_PERMISSIONS = "MANAGE_PERMISSIONS"


class PermissionInfo(AntaresBaseModel):
    owner: Optional[int] = None
    groups: List[str] = []
    public_mode: PublicMode = PublicMode.NONE

    @classmethod
    def from_study(cls, study: Union["Study", "StudyMetadataDTO"]) -> "PermissionInfo":
        return cls(
            owner=None if study.owner is None else study.owner.id,
            groups=[g.id for g in study.groups if g.id is not None],
            public_mode=PublicMode.NONE if study.public_mode is None else PublicMode(study.public_mode),
        )
