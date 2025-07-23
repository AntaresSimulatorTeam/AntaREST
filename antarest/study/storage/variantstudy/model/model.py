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
import datetime
import uuid
from typing import List, MutableSequence, Optional, Tuple, TypeAlias

import typing_extensions as te

from antarest.core.model import JSON
from antarest.core.serde import AntaresBaseModel
from antarest.study.model import StudyMetadataDTO, StudyVersionStr

LegacyDetailsDTO: TypeAlias = Tuple[str, bool, str]
"""
Legacy details DTO: triplet of name, output status and output message.
"""


class NewDetailsDTO(te.TypedDict):
    """
    New details DTO: dictionary with keys 'id', 'name', 'status' and 'msg'.

    Attributes:
        id: command identifier (UUID) if it exists.
        name: command name.
        status: command status (true or false).
        msg: command generation message or error message (if the status is false).
    """

    id: uuid.UUID
    name: str
    status: bool
    msg: str


DetailsDTO: TypeAlias = LegacyDetailsDTO | NewDetailsDTO


class GenerationResultInfoDTO(AntaresBaseModel):
    """
    Result information of a snapshot generation process.

    Attributes:
        success: A boolean indicating whether the generation process was successful.
        details: Objects containing detailed information about the generation process.
    """

    success: bool
    details: MutableSequence[DetailsDTO]
    should_invalidate_cache: bool


class CommandDTOAPI(AntaresBaseModel):
    """
    This class exposes a command inside the API.

    Attributes:
        id: The unique identifier of the command.
        action: The action to be performed by the command.
        args: The arguments for the command action.
        version: The version of the command.
    """

    id: Optional[str] = None
    action: str
    args: MutableSequence[JSON] | JSON
    version: int = 1
    user_name: Optional[str] = None
    updated_at: Optional[datetime.datetime] = None


class CommandDTO(AntaresBaseModel):
    """
    This class represents a command internally.

    Attributes:
        id: The unique identifier of the command.
        action: The action to be performed by the command.
        args: The arguments for the command action.
        version: The version of the command.
        study_version: The version of the study associated to the command.
        user_id: id of the author of the command.
        updated_at: The time the command was last updated.
    """

    id: Optional[str] = None
    action: str
    args: List[JSON] | JSON
    version: int = 1
    study_version: StudyVersionStr
    user_id: Optional[int] = None
    updated_at: Optional[datetime.datetime] = None

    def to_api(self, user_name: Optional[str] = None) -> CommandDTOAPI:
        data = self.model_dump(mode="json", exclude={"study_version", "user_id"})
        data["user_name"] = user_name
        return CommandDTOAPI.model_validate(data)

    def get_args_list(self) -> MutableSequence[JSON]:
        return self.args if isinstance(self.args, list) else [self.args]


class CommandResultDTO(AntaresBaseModel):
    """
    This class represents the result of a command.

    Attributes:
        study_id: The unique identifier of the study.
        id: The unique identifier of the command.
        success: A boolean indicating whether the command was successful.
        message: A message detailing the result of the command.
    """

    study_id: str
    id: str
    success: bool
    message: str


class VariantTreeDTO:
    """
    This class represents a variant tree structure.

    Attributes:
        node: The metadata of the study (ID, name, version, etc.).
        children: A list of variant children.
    """

    def __init__(self, node: StudyMetadataDTO, children: MutableSequence["VariantTreeDTO"]) -> None:
        # We are intentionally not using Pydantic’s `BaseModel` here to prevent potential
        # `RecursionError` exceptions that can occur with Pydantic versions before v2.
        self.node = node
        self.children = children or []
