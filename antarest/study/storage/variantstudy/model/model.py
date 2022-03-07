from typing import List, Tuple, Optional, Union

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


class CommandResultDTO(BaseModel):
    study_id: str
    id: str
    success: bool
    message: str


class VariantTreeDTO(BaseModel):
    node: StudyMetadataDTO
    children: List["VariantTreeDTO"]


VariantTreeDTO.update_forward_refs()
