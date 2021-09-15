from typing import Dict, List, Union, Any, Optional

from pydantic import validator

from antarest.matrixstore.model import MatrixData
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.model.command.utils import (
    validate_matrix,
    strip_matrix_protocol,
)
from antarest.study.storage.variantstudy.model.model import CommandDTO
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
    values: Optional[Union[List[List[MatrixData]], str]] = None
    comments: Optional[str] = None

    def __init__(self, **data: Any) -> None:
        super().__init__(
            command_name=CommandName.UPDATE_BINDING_CONSTRAINT,
            version=1,
            **data,
        )

    @validator("values", always=True)
    def validate_series(
        cls, v: Optional[Union[List[List[MatrixData]], str]], values: Any
    ) -> Optional[Union[List[List[MatrixData]], str]]:
        if v is None:
            v = values[
                "command_context"
            ].generator_matrix_constants.get_null_matrix()
            return v
        else:
            return validate_matrix(v, values)

    def _apply(self, study_data: FileStudy) -> CommandOutput:
        raise NotImplementedError()

    def to_dto(self) -> CommandDTO:
        return CommandDTO(
            action=CommandName.UPDATE_BINDING_CONSTRAINT.value,
            args={
                "id": self.id,
                "name": self.name,
                "enabled": self.enabled,
                "time_step": self.time_step.value,
                "operator": self.operator.value,
                "coeffs": self.coeffs,
                "values": strip_matrix_protocol(self.values),
                "comments": self.comments,
            },
        )
