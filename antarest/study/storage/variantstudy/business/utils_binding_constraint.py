from typing import Optional, Dict, List, Union

from antarest.core.model import JSON
from antarest.matrixstore.model import MatrixData
from antarest.study.storage.rawstudy.model.filesystem.config.model import (
    BindingConstraintDTO,
    FileStudyTreeConfig,
)
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.model.command.common import (
    TimeStep,
    BindingConstraintOperator,
    CommandOutput,
)


def cluster_does_not_exist(
    study_data: FileStudy, area: str, thermal_id: str
) -> bool:
    return area not in study_data.config.areas or thermal_id not in [
        thermal.id for thermal in study_data.config.areas[area].thermals
    ]


def link_does_not_exist(
    study_data: FileStudy, area_1: str, area_2: str
) -> bool:
    return (
        area_1 not in study_data.config.areas
        or area_2 not in study_data.config.areas[area_1].links
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
        "name": name,
        "id": bd_id,
        "enabled": enabled,
        "type": time_step.value,
        "operator": operator.value,
    }
    if comments is not None:
        binding_constraints[str(new_key)]["comments"] = comments

    for link_or_thermal in coeffs:
        if "%" in link_or_thermal:
            area_1, area_2 = link_or_thermal.split("%")
            if link_does_not_exist(study_data, area_1, area_2):
                return CommandOutput(
                    status=False,
                    message=f"Link {link_or_thermal} does not exist",
                )
        else:
            area, thermal_id = link_or_thermal.split(".")
            if cluster_does_not_exist(study_data, area, thermal_id):
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
    parse_bindings_coeffs_and_save_into_config(
        bd_id, study_data.config, coeffs
    )
    study_data.tree.save(
        binding_constraints,
        ["input", "bindingconstraints", "bindingconstraints"],
    )
    if values:
        assert isinstance(values, str)
        study_data.tree.save(values, ["input", "bindingconstraints", bd_id])
    return CommandOutput(status=True)


def parse_bindings_coeffs_and_save_into_config(
    bd_id: str,
    study_data_config: FileStudyTreeConfig,
    coeffs: Dict[str, List[float]],
) -> None:
    if bd_id not in [bind.id for bind in study_data_config.bindings]:
        areas_set = set()
        clusters_set = set()
        for k, v in coeffs.items():
            if "%" in k:
                areas_set.add(k.split("%")[0])
                areas_set.add(k.split("%")[1])
            elif "." in k:
                clusters_set.add(k)
                areas_set.add(k.split(".")[0])
        study_data_config.bindings.append(
            BindingConstraintDTO(
                id=bd_id, areas=areas_set, clusters=clusters_set
            )
        )


def remove_area_cluster_from_binding_constraints(
    study_data_config: FileStudyTreeConfig,
    area_id: str,
    cluster_id: Optional[str] = None,
) -> None:
    for binding in study_data_config.bindings:
        if (cluster_id and f"{area_id}.{cluster_id}" in binding.clusters) or (
            not cluster_id and area_id in binding.areas
        ):
            study_data_config.bindings.remove(binding)
