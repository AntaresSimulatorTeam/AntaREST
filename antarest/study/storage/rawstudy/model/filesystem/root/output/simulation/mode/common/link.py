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
from typing_extensions import override

from antarest.matrixstore.uri_resolver_service import UriResolverService
from antarest.study.storage.rawstudy.model.filesystem.config.model import FileStudyTreeConfig
from antarest.study.storage.rawstudy.model.filesystem.folder_node import FolderNode
from antarest.study.storage.rawstudy.model.filesystem.inode import TREE
from antarest.study.storage.rawstudy.model.filesystem.matrix.matrix import MatrixFrequency
from antarest.study.storage.rawstudy.model.filesystem.matrix.output_series_matrix import LinkOutputSeriesMatrix


class OutputSimulationLinkItem(FolderNode):
    def __init__(
        self,
        context: UriResolverService,
        config: FileStudyTreeConfig,
        area: str,
        link: str,
    ):
        super().__init__(context, config)
        self.area = area
        self.link = link

    @override
    def build(self) -> TREE:
        children: TREE = {}
        freq: MatrixFrequency
        for freq in MatrixFrequency:
            for output_type in ["id", "values"]:
                file_name = f"{output_type}-{freq}.txt"
                if (self.config.path / file_name).exists():
                    children[f"{output_type}-{freq}"] = LinkOutputSeriesMatrix(
                        self.context,
                        self.config.next_file(file_name),
                        freq,
                        self.area,
                        self.link,
                    )

        return children
