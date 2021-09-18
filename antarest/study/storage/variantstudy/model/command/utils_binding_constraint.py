from typing import Optional, Dict, List, Union

from antarest.core.custom_types import JSON
from antarest.matrixstore.model import MatrixData
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.model.command.common import (
    TimeStep,
    BindingConstraintOperator,
    CommandOutput,
)


def apply_binding_constraint(
    study_data: FileStudy,
    binding_constraints: JSON,
    new_key: str,
    bd_id: str,
    name: str,
    comments: Optional[str],
    enabled: bool,
    time_step: TimeStep,
    operator: BindingConstraintOperator,
    coeffs: Dict[str, List[float]],
    values: Optional[Union[List[List[MatrixData]], str]],
) -> CommandOutput:
    binding_constraints[str(new_key)] = {
        "id": bd_id,
        "name": name,
        "enabled": enabled,
        "type": time_step.value,
        "operator": operator.value,
    }
    if comments is not None:
        binding_constraints[str(new_key)]["comments"] = comments

    for link_or_thermal in coeffs:
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
        if len(coeffs[link_or_thermal]) == 2:
            coeffs[link_or_thermal][1] = int(coeffs[link_or_thermal][1])

        binding_constraints[str(new_key)][link_or_thermal] = "%".join(
            [str(coeff_val) for coeff_val in coeffs[link_or_thermal]]
        )

    study_data.config.bindings.append(bd_id)
    study_data.tree.save(
        binding_constraints,
        ["input", "bindingconstraints", "bindingconstraints"],
    )
    if values:
        assert isinstance(values, str)
        study_data.tree.save(values, ["input", "bindingconstraints", bd_id])
    return CommandOutput(status=True)
