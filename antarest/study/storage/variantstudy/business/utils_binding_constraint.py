import typing as t

from antarest.study.storage.rawstudy.model.filesystem.config.binding_constraint import BindingConstraintFrequency
from antarest.study.storage.rawstudy.model.filesystem.config.model import BindingConstraintDTO, FileStudyTreeConfig


def parse_bindings_coeffs_and_save_into_config(
    bd_id: str,
    study_data_config: FileStudyTreeConfig,
    coeffs: t.Mapping[str, t.Union[t.Literal["hourly", "daily", "weekly"], t.Sequence[float]]],
    group: str,
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
            BindingConstraintDTO(
                id=bd_id,
                areas=areas_set,
                clusters=clusters_set,
                time_step=time_step,
                group=group,
            )
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
