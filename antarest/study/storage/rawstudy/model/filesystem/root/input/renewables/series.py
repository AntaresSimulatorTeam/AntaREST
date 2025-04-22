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

from antarest.matrixstore.uri_resolver_service import MatrixUriMapper
from antarest.study.storage.rawstudy.model.filesystem.config.model import FileStudyTreeConfig
from antarest.study.storage.rawstudy.model.filesystem.folder_node import FolderNode
from antarest.study.storage.rawstudy.model.filesystem.inode import TREE
from antarest.study.storage.rawstudy.model.filesystem.matrix.constants import default_scenario_hourly
from antarest.study.storage.rawstudy.model.filesystem.matrix.input_series_matrix import InputSeriesMatrix


class ClusteredRenewableSeries(FolderNode):
    @override
    def build(self) -> TREE:
        series_config = self.config.next_file("series.txt")
        children: TREE = {
            "series": InputSeriesMatrix(
                self.matrix_mapper,
                series_config,
                default_empty=default_scenario_hourly,
            )
        }
        return children


class ClusteredRenewableClusterSeries(FolderNode):
    def __init__(
        self,
        matrix_mapper: MatrixUriMapper,
        config: FileStudyTreeConfig,
        area: str,
    ):
        super().__init__(matrix_mapper, config)
        self.area = area

    @override
    def build(self) -> TREE:
        # Note that cluster IDs may not be in lower case, but series IDs are.
        series_ids = map(str.lower, self.config.get_renewable_ids(self.area))
        children: TREE = {
            series_id: ClusteredRenewableSeries(self.matrix_mapper, self.config.next_file(series_id))
            for series_id in series_ids
        }
        return children


class ClusteredRenewableAreaSeries(FolderNode):
    @override
    def build(self) -> TREE:
        return {
            area: ClusteredRenewableClusterSeries(self.matrix_mapper, self.config.next_file(area), area)
            for area in self.config.area_names()
        }
