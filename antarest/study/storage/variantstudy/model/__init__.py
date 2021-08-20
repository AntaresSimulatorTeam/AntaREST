from typing import Tuple, List, Optional, Union

from pydantic.main import BaseModel

from antarest.core.custom_types import JSON


class GenerationResultInfoDTO(BaseModel):
    success: bool
    details: List[Tuple[str, bool, str]]


class CommandDTO(BaseModel):
    id: Optional[str]
    action: str
    # if args is a list, this mean the command will be mapped to the list of args
    args: Union[JSON, List[JSON]]
