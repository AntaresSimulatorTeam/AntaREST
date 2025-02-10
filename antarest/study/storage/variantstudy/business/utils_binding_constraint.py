# Copyright (c) 2025, RTE (https://www.rte-france.com)
#
# See AUTHORS.txt
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# SPDX-License-Identifier: MPL-2.0
#
# This file is part of the Antares project.

from typing import Literal, Mapping, Sequence

from antarest.study.storage.rawstudy.model.filesystem.config.binding_constraint import (
    BindingConstraintFrequency,
    BindingConstraintOperator,
)
from antarest.study.storage.rawstudy.model.filesystem.config.model import BindingConstraintDTO, FileStudyTreeConfig


def parse_bindings_coeffs_and_save_into_config(
    bd_id: str,
    study_data_config: FileStudyTreeConfig,
    coeffs: Mapping[str, Literal["hourly", "daily", "weekly"] | Sequence[float]],
    operator: BindingConstraintOperator,
    time_step: BindingConstraintFrequency,
    group: str,
) -> None:
    if bd_id not in [bind.id for bind in study_data_config.bindings]:
        areas_set = set()
        clusters_set = set()
        for k, v in coeffs.items():
            if "%" in k:
                areas_set |= set(k.split("%"))
            elif "." in k:
                clusters_set.add(k)
                areas_set.add(k.split(".")[0])
        bc = BindingConstraintDTO(
            id=bd_id,
            group=group,
            areas=areas_set,
            clusters=clusters_set,
            operator=operator,
            time_step=time_step,
        )
        study_data_config.bindings.append(bc)


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
