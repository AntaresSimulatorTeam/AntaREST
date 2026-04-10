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
from typing import Any

from typing_extensions import override

from antarest.matrixstore.matrix_uri_mapper import MatrixUriMapper
from antarest.study.storage.rawstudy.model.filesystem.config.model import FileStudyTreeConfig
from antarest.study.storage.rawstudy.model.filesystem.folder_node import FolderNode
from antarest.study.storage.rawstudy.model.filesystem.inode import TREE, INode
from antarest.study.storage.rawstudy.model.filesystem.matrix.input_series_matrix import InputSeriesMatrix
from antarest.study.storage.rawstudy.model.filesystem.root.input.reserves.reserves_ini import InputReservesIni


class InputReservesAreaFolder(FolderNode):
    """Folder node for a single area's reserves: input/reserves/{area_id}/

    For version >= 10.0, both the legacy matrix (input/reserves/{area_id}.txt)
    and the new reserves.ini (input/reserves/{area_id}/reserves.ini) coexist.
    When accessed directly via get_node(), returns the matrix node so that
    existing matrix reading code (get_matrix, raw_path_to_matrix_mapper) keeps working.
    When navigated deeper (e.g. ["reserves"]), delegates to folder children.
    """

    def __init__(
        self,
        matrix_mapper: MatrixUriMapper,
        config: FileStudyTreeConfig,
        matrix_node: InputSeriesMatrix,
    ):
        super().__init__(matrix_mapper, config)
        self._matrix_node = matrix_node

    @override
    def build(self) -> TREE:
        return {
            self._matrix_node.config.path.stem: self._matrix_node,
            "reserves": InputReservesIni(self.config.next_file("reserves.ini")),
        }

    @override
    def get_node_and_remainder(
        self,
        url: list[str] | None = None,
    ) -> tuple[INode[Any, Any, Any], list[str]]:
        if not url:
            return self._matrix_node, []
        return super().get_node_and_remainder(url)

    @override
    def save(self, data: Any, url: list[str] | None = None) -> None:
        if not url:
            return self._matrix_node.save(data)
        return super().save(data, url)

    @override
    def delete(self, url: list[str] | None = None) -> None:
        if not url:
            return self._matrix_node.delete()
        return super().delete(url)
