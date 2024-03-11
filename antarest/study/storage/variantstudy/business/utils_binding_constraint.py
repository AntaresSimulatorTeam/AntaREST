from typing import Dict, List, Literal, Mapping, Optional, Sequence, Union

from antarest.core.model import JSON
from antarest.matrixstore.model import MatrixData
from antarest.study.storage.rawstudy.model.filesystem.config.binding_constraint import (
    BindingConstraintDTO,
    BindingConstraintFrequency,
)
from antarest.study.storage.rawstudy.model.filesystem.config.model import FileStudyTreeConfig
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.model.command.common import BindingConstraintOperator, CommandOutput


def apply_binding_constraint(
    study_data: FileStudy,
    binding_constraints: JSON,
    new_key: str,
    bd_id: str,
    name: str,
    comments: Optional[str],
    enabled: bool,
    freq: BindingConstraintFrequency,
    operator: BindingConstraintOperator,
    coeffs: Dict[str, List[float]],
    values: Optional[Union[List[List[MatrixData]], str]],
    less_term_matrix: Optional[Union[List[List[MatrixData]], str]],
    greater_term_matrix: Optional[Union[List[List[MatrixData]], str]],
    equal_term_matrix: Optional[Union[List[List[MatrixData]], str]],
    filter_year_by_year: Optional[str] = None,
    filter_synthesis: Optional[str] = None,
    group: Optional[str] = None,
) -> CommandOutput:
    version = study_data.config.version
    binding_constraints[new_key] = {
        "name": name,
        "id": bd_id,
        "enabled": enabled,
        "type": freq.value,
        "operator": operator.value,
    }
    if group:
        binding_constraints[new_key]["group"] = group
    if version >= 830:
        if filter_year_by_year:
            binding_constraints[new_key]["filter-year-by-year"] = filter_year_by_year
        if filter_synthesis:
            binding_constraints[new_key]["filter-synthesis"] = filter_synthesis
    if comments is not None:
        binding_constraints[new_key]["comments"] = comments

    for link_or_cluster in coeffs:
        if "%" in link_or_cluster:
            area_1, area_2 = link_or_cluster.split("%")
            if area_1 not in study_data.config.areas or area_2 not in study_data.config.areas[area_1].links:
                return CommandOutput(
                    status=False,
                    message=f"Link '{link_or_cluster}' does not exist in binding constraint '{bd_id}'",
                )
        elif "." in link_or_cluster:
            # Cluster IDs are stored in lower case in the binding constraints file.
            area, cluster_id = link_or_cluster.split(".")
            thermal_ids = {thermal.id.lower() for thermal in study_data.config.areas[area].thermals}
            if area not in study_data.config.areas or cluster_id.lower() not in thermal_ids:
                return CommandOutput(
                    status=False,
                    message=f"Cluster '{link_or_cluster}' does not exist in binding constraint '{bd_id}'",
                )
        else:
            raise NotImplementedError(f"Invalid link or thermal ID: {link_or_cluster}")

        # this is weird because Antares Simulator only accept int as offset
        if len(coeffs[link_or_cluster]) == 2:
            coeffs[link_or_cluster][1] = int(coeffs[link_or_cluster][1])

        binding_constraints[new_key][link_or_cluster] = "%".join(
            [str(coeff_val) for coeff_val in coeffs[link_or_cluster]]
        )
    parse_bindings_coeffs_and_save_into_config(bd_id, study_data.config, coeffs)
    study_data.tree.save(
        binding_constraints,
        ["input", "bindingconstraints", "bindingconstraints"],
    )
    if values:
        if not isinstance(values, str):  # pragma: no cover
            raise TypeError(repr(values))
        if version < 870:
            study_data.tree.save(values, ["input", "bindingconstraints", bd_id])
    for matrix_term, matrix_name, matrix_alias in zip(
        [less_term_matrix, greater_term_matrix, equal_term_matrix],
        ["less_term_matrix", "greater_term_matrix", "equal_term_matrix"],
        ["lt", "gt", "eq"],
    ):
        if matrix_term:
            if not isinstance(matrix_term, str):  # pragma: no cover
                raise TypeError(repr(matrix_term))
            if version >= 870:
                study_data.tree.save(matrix_term, ["input", "bindingconstraints", f"{bd_id}_{matrix_alias}"])
    return CommandOutput(status=True)


def parse_bindings_coeffs_and_save_into_config(
    bd_id: str,
    study_data_config: FileStudyTreeConfig,
    coeffs: Mapping[str, Union[Literal["hourly", "daily", "weekly"], Sequence[float]]],
) -> None:
    if bd_id not in [bind.id for bind in study_data_config.bindings]:
        areas_set = set()
        clusters_set = set()
        # Default time_step value
        time_step = BindingConstraintFrequency.HOURLY
        for k, v in coeffs.items():
            if k == "type":
                time_step = BindingConstraintFrequency(v)
            if "%" in k:
                areas_set |= set(k.split("%"))
            elif "." in k:
                clusters_set.add(k)
                areas_set.add(k.split(".")[0])
        study_data_config.bindings.append(
            BindingConstraintDTO(id=bd_id, areas=areas_set, clusters=clusters_set, time_step=time_step)
        )


def remove_area_cluster_from_binding_constraints(
    study_data_config: FileStudyTreeConfig,
    area_id: str,
    cluster_id: str = "",
) -> None:
    if cluster_id:
        # Cluster IDs are stored in lower case in the binding constraints file.
        cluster_id = cluster_id.lower()
        selection = [b for b in study_data_config.bindings if f"{area_id}.{cluster_id}" in b.clusters]
    else:
        selection = [b for b in study_data_config.bindings if area_id in b.areas]
    for binding in selection:
        study_data_config.bindings.remove(binding)
