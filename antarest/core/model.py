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

import enum
from typing import TYPE_CHECKING, Annotated, Any, TypeAlias

from pydantic import BeforeValidator, StringConstraints

from antarest.core.serde import AntaresBaseModel
from antarest.study.storage.rawstudy.model.filesystem.config.identifier import transform_name_to_id

if TYPE_CHECKING:
    # These dependencies are only used for type checking with mypy.
    from antarest.study.model import Study, StudyMetadataDTO

JSON: TypeAlias = dict[str, Any]
ELEMENT: TypeAlias = str | int | float | bool | bytes
SUB_JSON: TypeAlias = ELEMENT | JSON | list[Any] | None
LowerCaseStr: TypeAlias = Annotated[str, StringConstraints(to_lower=True)]
LowerCaseId: TypeAlias = Annotated[str, BeforeValidator(lambda x: transform_name_to_id(x, lower=True))]


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
    owner: int | None = None
    groups: list[str] = []
    public_mode: PublicMode = PublicMode.NONE

    @classmethod
    def from_study(cls, study: "Study | StudyMetadataDTO") -> "PermissionInfo":
        return cls(
            owner=None if study.owner is None else study.owner.id,
            groups=[g.id for g in study.groups if g.id is not None],
            public_mode=PublicMode.NONE if study.public_mode is None else PublicMode(study.public_mode),
        )
