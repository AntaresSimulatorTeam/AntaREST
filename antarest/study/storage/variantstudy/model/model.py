import typing as t
import uuid

import typing_extensions as te
from pydantic import BaseModel

from antarest.core.model import JSON
from antarest.study.model import StudyMetadataDTO

LegacyDetailsDTO = t.Tuple[str, bool, str]
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


DetailsDTO = t.Union[LegacyDetailsDTO, NewDetailsDTO]


class GenerationResultInfoDTO(BaseModel):
    """
    Result information of a snapshot generation process.

    Attributes:
        success: A boolean indicating whether the generation process was successful.
        details: Objects containing detailed information about the generation process.
    """

    success: bool
    details: t.MutableSequence[DetailsDTO]


class CommandDTO(BaseModel):
    """
    This class represents a command.

    Attributes:
        id: The unique identifier of the command.
        action: The action to be performed by the command.
        args: The arguments for the command action.
        version: The version of the command.
    """

    id: t.Optional[str]
    action: str
    args: t.Union[t.MutableSequence[JSON], JSON]
    version: int = 1


class CommandResultDTO(BaseModel):
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

    def __init__(self, node: StudyMetadataDTO, children: t.MutableSequence["VariantTreeDTO"]) -> None:
        # We are intentionally not using Pydantic’s `BaseModel` here to prevent potential
        # `RecursionError` exceptions that can occur with Pydantic versions before v2.
        self.node = node
        self.children = children or []
