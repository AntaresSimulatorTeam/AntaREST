from typing import Tuple, List, Optional, Union

from pydantic.main import BaseModel

from antarest.core.custom_types import JSON
from antarest.study.storage.variantstudy.model.command.icommand import ICommand


class GenerationResultInfoDTO(BaseModel):
    success: bool
    details: List[Tuple[str, bool, str]]


class Command(BaseModel):
    id: str
    action: ICommand
    args: JSON


class CommandDTO(BaseModel):
    id: Optional[str]
    action: str
    # if args is a list, this mean the command will be mapped to the list of args
    args: Union[JSON, List[JSON]]
