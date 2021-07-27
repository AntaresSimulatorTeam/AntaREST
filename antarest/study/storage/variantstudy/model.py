from typing import List, Tuple, Optional

from pydantic import BaseModel

from antarest.core.custom_types import JSON


class CommandDTO(BaseModel):
    id: Optional[str]
    action: str
    args: JSON


class GenerationResultInfoDTO(BaseModel):
    success: bool
    details: List[Tuple[str, bool, str]]