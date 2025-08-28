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
from enum import StrEnum
from pathlib import PurePosixPath
from typing import Self

from pydantic import model_validator

from antarest.core.serde import AntaresBaseModel


class ResourceType(StrEnum):
    FILE = "file"
    FOLDER = "folder"


class CreateUserResourceData(AntaresBaseModel):
    path: PurePosixPath
    resource_type: ResourceType
    content: bytes | None = None

    @model_validator(mode="after")
    def _validate_coherence(self) -> Self:
        if self.resource_type == ResourceType.FOLDER and self.content is not None:
            raise ValueError("You cannot provide a content for a folder")
        return self


class RemoveUserResourceData(AntaresBaseModel):
    path: str
