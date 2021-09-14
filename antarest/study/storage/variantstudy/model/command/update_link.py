from typing import Dict, List, Union, Any, Optional

from pydantic import validator

from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.model.command.utils import (
    validate_matrix,
    strip_matrix_protocol,
)
from antarest.study.storage.variantstudy.model.model import CommandDTO
from antarest.study.storage.variantstudy.model.command.common import (
    CommandOutput,
    CommandName,
)
from antarest.study.storage.variantstudy.model.command.icommand import ICommand


class UpdateLink(ICommand):
    area1: str
    area2: str
    parameters: Dict[str, str]
    series: Optional[Union[List[List[float]], str]] = None

    def __init__(self, **data: Any) -> None:
        super().__init__(
            command_name=CommandName.UPDATE_LINK, version=1, **data
        )

    @validator("series", always=True)
    def validate_series(
        cls, v: Optional[Union[List[List[float]], str]], values: Any
    ) -> Optional[Union[List[List[float]], str]]:
        if v is None:
            v = values["command_context"].generator_matrix_constants.get_link()
            return v
        else:
            return validate_matrix(v, values)

    def _apply(self, study_data: FileStudy) -> CommandOutput:
        raise NotImplementedError()

    def to_dto(self) -> CommandDTO:
        return CommandDTO(
            action=CommandName.UPDATE_LINK.value,
            args={
                "area1": self.area1,
                "area2": self.area2,
                "parameters": self.parameters,
                "series": strip_matrix_protocol(self.series),
            },
        )
