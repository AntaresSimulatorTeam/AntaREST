from typing import Dict, List, Union

from pydantic import validator

from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.model.command.common import (
    CommandOutput,
    CommandName,
)
from antarest.study.storage.variantstudy.model.command.icommand import ICommand
from antarest.study.storage.variantstudy.model.command_context import (
    CommandContext,
)


class UpdateBindingConstraint(ICommand):
    id: str
    name: str
    enabled: bool
    time_step: str
    operator: str
    coeffs: List[Dict[str, Union[str, float]]]
    values: Union[List[List[float]], str]

    def __init__(self) -> None:
        super().__init__(
            command_name=CommandName.UPDATE_BINDING_CONSTRAINT, version=1
        )

    @validator("time_step")
    def check_time_step(self, v: str) -> str:
        if v not in ["hourly", "daily", "weekly"]:
            raise ValueError(
                "Time step must be either hourly, daily or weekly"
            )
        return v

    @validator("operator")
    def check_operator(self, v: str) -> str:
        if v not in ["both", "equal", "greater", "less"]:
            raise ValueError(
                "Operator must be either both, equal, greater or less"
            )
        return v

    @validator("coeffs")
    def check_coeffs(
        self, v: List[Dict[str, Union[str, float]]]
    ) -> List[Dict[str, Union[str, float]]]:
        if not isinstance(v, list):
            raise ValueError("Coeffs must be a list")
        try:
            for d in v:
                if d["type"] not in ["thermal", "link"]:
                    raise ValueError(
                        "Coeffs type must be either thermal or link"
                    )
            return v
        except:
            raise ValueError("Coeffs is wrong")

    def apply(
        self, study_data: FileStudy, command_context: CommandContext
    ) -> CommandOutput:
        raise NotImplementedError()

    def revert(self, study_data: FileStudy) -> CommandOutput:
        raise NotImplementedError()
