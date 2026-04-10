# Copyright (c) 2026, RTE (https://www.rte-france.com)
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
from typing import TYPE_CHECKING, Callable

from antarest.core.exceptions import AreaNotFound
from antarest.study.dao.common import AreaId, AreaSeriesMapping
from antarest.study.storage.rawstudy.model.filesystem.config.model import FileStudyTreeConfig
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.rawstudy.model.filesystem.matrix.matrix import MatrixNode

if TYPE_CHECKING:
    from antarest.study.dao.file.file_study_dao import FileStudyTreeDao


def check_area_exists(study_data: FileStudyTreeConfig, area_id: str) -> None:
    if area_id not in study_data.areas:
        raise AreaNotFound(f"The area '{area_id}' does not exist")


def get_all_area_matrices(
    file_study_dao: "FileStudyTreeDao", study_data: FileStudy, url_getter: Callable[[AreaId], list[str]]
) -> AreaSeriesMapping:
    matrix_nodes = {}

    areas = study_data.config.areas
    for area_id in areas:
        url = url_getter(area_id)
        node = study_data.tree.get_node(url)
        assert isinstance(node, MatrixNode)
        matrix_nodes[node] = area_id

    result: AreaSeriesMapping = {}

    matrices_mapping = file_study_dao.get_matrices_ids(list(matrix_nodes))

    for node, matrix_id in matrices_mapping.items():
        area_id = matrix_nodes[node]
        result[area_id] = matrix_id

    return result
