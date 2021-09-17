from typing import Dict, List, Union, Any, Optional

from pydantic import validator

from antarest.matrixstore.model import MatrixData
from antarest.study.storage.rawstudy.model.filesystem.config.model import (
    transform_name_to_id,
)
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.model.model import CommandDTO
from antarest.study.storage.variantstudy.model.command.common import (
    CommandOutput,
    CommandName,
    BindingConstraintOperator,
    TimeStep,
)
from antarest.study.storage.variantstudy.model.command.icommand import ICommand
from antarest.study.storage.variantstudy.model.command.utils import (
    validate_matrix,
    strip_matrix_protocol,
)


class CreateBindingConstraint(ICommand):
    name: str
    enabled: bool = True
    time_step: TimeStep
    operator: BindingConstraintOperator
    coeffs: Dict[str, List[float]]
    values: Optional[Union[List[List[MatrixData]], str]] = None
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

    def _apply(self, study_data: FileStudy) -> CommandOutput:
        assert isinstance(self.values, str)
        binding_constraints = study_data.tree.get(
            ["input", "bindingconstraints", "bindingconstraints"]
        )

        new_key = len(binding_constraints.keys())
        bd_id = transform_name_to_id(self.name)
        binding_constraints[str(new_key)] = {
            "id": bd_id,
            "name": self.name,
            "enabled": self.enabled,
            "type": self.time_step.value,
            "operator": self.operator.value,
        }
        if self.comments is not None:
            binding_constraints[str(new_key)]["comments"] = self.comments

        for link_or_thermal in self.coeffs:
            if "%" in link_or_thermal:
                area_1, area_2 = link_or_thermal.split("%")
                if (
                    area_1 not in study_data.config.areas
                    or area_2 not in study_data.config.areas[area_1].links
                ):
                    return CommandOutput(
                        status=False,
                        message=f"Link {link_or_thermal} does not exist",
                    )
            else:
                area, thermal_id = link_or_thermal.split(".")
                if area not in study_data.config.areas or thermal_id not in [
                    thermal.id
                    for thermal in study_data.config.areas[area].thermals
                ]:
                    return CommandOutput(
                        status=False,
                        message=f"Thermal cluster {link_or_thermal} does not exist",
                    )

            # this is weird because Antares Simulator only accept int as offset
            if len(self.coeffs[link_or_thermal]) == 2:
                self.coeffs[link_or_thermal][1] = int(
                    self.coeffs[link_or_thermal][1]
                )

            binding_constraints[str(new_key)][link_or_thermal] = "%".join(
                [str(coeff_val) for coeff_val in self.coeffs[link_or_thermal]]
            )

        study_data.config.bindings.append(bd_id)
        study_data.tree.save(
            binding_constraints,
            ["input", "bindingconstraints", "bindingconstraints"],
        )
        study_data.tree.save(
            self.values, ["input", "bindingconstraints", bd_id]
        )

        return CommandOutput(status=True)

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
            },
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

    def revert(self, history: List["ICommand"], base: FileStudy) -> Optional["ICommand"]:
        return None
