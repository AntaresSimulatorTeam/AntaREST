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
from enum import StrEnum
from pathlib import PurePosixPath
from typing import Self

from pydantic import model_validator

from antarest.core.serde import AntaresBaseModel


class ResourceType(StrEnum):
    FILE = "file"
    FOLDER = "folder"


class UserResourceDataCreation(AntaresBaseModel):
    path: PurePosixPath
    resource_type: ResourceType
    blob_id: str | None = None

    @model_validator(mode="after")
    def _validate_coherence(self) -> Self:
        if self.resource_type == ResourceType.FOLDER and self.blob_id is not None:
            raise ValueError("You cannot provide a blob_id for a folder")
        return self


class UserResourceDataRemoval(AntaresBaseModel):
    path: str
