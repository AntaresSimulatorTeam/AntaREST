from typing import Any, Dict, List, Optional, Tuple, Union, cast

from pydantic import validator

from antarest.core.utils.utils import assert_this
from antarest.matrixstore.model import MatrixData
from antarest.study.storage.rawstudy.model.filesystem.config.model import (
    FileStudyTreeConfig,
    transform_name_to_id,
)
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.business.utils import (
    strip_matrix_protocol,
    validate_matrix,
)
from antarest.study.storage.variantstudy.business.utils_binding_constraint import (
    apply_binding_constraint,
    parse_bindings_coeffs_and_save_into_config,
)
from antarest.study.storage.variantstudy.model.command.common import (
    BindingConstraintOperator,
    CommandName,
    CommandOutput,
    TimeStep,
)
from antarest.study.storage.variantstudy.model.command.icommand import (
    MATCH_SIGNATURE_SEPARATOR,
    ICommand,
)
from antarest.study.storage.variantstudy.model.model import CommandDTO


class CreateBindingConstraint(ICommand):
    name: str
    enabled: bool = True
    time_step: TimeStep
    operator: BindingConstraintOperator
    coeffs: Dict[str, List[float]]
    values: Optional[Union[List[List[MatrixData]], str]] = None
    filter_year_by_year: Optional[str] = None
    filter_synthesis: Optional[str] = None
    comments: Optional[str] = None

    def __init__(self, **data: Any) -> None:
        super().__init__(
            command_name=CommandName.CREATE_BINDING_CONSTRAINT,
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

    def _apply_config(
        self, study_data_config: FileStudyTreeConfig
    ) -> Tuple[CommandOutput, Dict[str, Any]]:
        bd_id = transform_name_to_id(self.name)
        parse_bindings_coeffs_and_save_into_config(
            bd_id, study_data_config, self.coeffs
        )
        return CommandOutput(status=True), {}

    def _apply(self, study_data: FileStudy) -> CommandOutput:
        assert_this(isinstance(self.values, str))
        binding_constraints = study_data.tree.get(
            ["input", "bindingconstraints", "bindingconstraints"]
        )
        new_key = len(binding_constraints.keys())
        bd_id = transform_name_to_id(self.name)
        return apply_binding_constraint(
            study_data,
            binding_constraints,
            str(new_key),
            bd_id,
            self.name,
            self.comments,
            self.enabled,
            self.time_step,
            self.operator,
            self.coeffs,
            self.values,
            self.filter_year_by_year,
            self.filter_synthesis,
        )

    def to_dto(self) -> CommandDTO:
        return CommandDTO(
            action=CommandName.CREATE_BINDING_CONSTRAINT.value,
            args={
                "name": self.name,
                "enabled": self.enabled,
                "time_step": self.time_step.value,
                "operator": self.operator.value,
                "coeffs": self.coeffs,
                "values": strip_matrix_protocol(self.values),
                "comments": self.comments,
                "filter_year_by_year": self.filter_year_by_year,
                "filter_synthesis": self.filter_synthesis,
            },
        )

    def match_signature(self) -> str:
        return str(
            self.command_name.value + MATCH_SIGNATURE_SEPARATOR + self.name
        )

    def match(self, other: ICommand, equal: bool = False) -> bool:
        if not isinstance(other, CreateBindingConstraint):
            return False
        simple_match = self.name == other.name
        if not equal:
            return simple_match
        return (
            simple_match
            and self.enabled == other.enabled
            and self.time_step == other.time_step
            and self.operator == other.operator
            and self.coeffs == other.coeffs
            and self.values == other.values
            and self.comments == other.comments
        )

    def _create_diff(self, other: "ICommand") -> List["ICommand"]:
        other = cast(CreateBindingConstraint, other)
        from antarest.study.storage.variantstudy.model.command.update_binding_constraint import (
            UpdateBindingConstraint,
        )

        bd_id = transform_name_to_id(self.name)
        return [
            UpdateBindingConstraint(
                id=bd_id,
                enabled=other.enabled,
                time_step=other.time_step,
                operator=other.operator,
                coeffs=other.coeffs,
                values=strip_matrix_protocol(other.values)
                if self.values != other.values
                else None,
                filter_year_by_year=other.filter_year_by_year,
                filter_synthesis=other.filter_synthesis,
                comments=other.comments,
                command_context=other.command_context,
            )
        ]

    def get_inner_matrices(self) -> List[str]:
        if self.values is not None:
            assert_this(isinstance(self.values, str))
            return [strip_matrix_protocol(self.values)]
        return []
