from typing import Dict, List, Union, Any

from pydantic import validator

from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.model.command.common import (
    CommandOutput,
    CommandName,
    BindingConstraintOperator,
    TimeStep,
)
from antarest.study.storage.variantstudy.model.command.icommand import ICommand


class UpdateBindingConstraint(ICommand):
    id: str
    name: str
    enabled: bool
    time_step: TimeStep
    operator: BindingConstraintOperator
    coeffs: Dict[str, List[float]]
    values: Union[List[List[float]], str]

    def __init__(self, **data: Any) -> None:
        super().__init__(
            command_name=CommandName.UPDATE_BINDING_CONSTRAINT,
            version=1,
            **data,
        )

    def _apply(self, study_data: FileStudy) -> CommandOutput:
        raise NotImplementedError()

    def revert(self, study_data: FileStudy) -> CommandOutput:
        raise NotImplementedError()
