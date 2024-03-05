from typing import List, Optional, Tuple, Union

from pydantic import BaseModel

from antarest.core.model import JSON
from antarest.study.model import StudyMetadataDTO


class GenerationResultInfoDTO(BaseModel):
    success: bool
    details: List[Tuple[str, bool, str]]


class CommandDTO(BaseModel):
    id: Optional[str]
    action: str
    # if args is a list, this mean the command will be mapped to the list of args
    args: Union[List[JSON], JSON]
    version: int = 1


class CommandResultDTO(BaseModel):
    study_id: str
    id: str
    success: bool
    message: str


class VariantTreeDTO:
    # Don't use BaseModel as this could trigger Recursion exceptions, since we're using Pydantic with a version prior to v2.
    def __init__(self, node: StudyMetadataDTO, children: List["VariantTreeDTO"]) -> None:
        self.node = node
        self.children = children
