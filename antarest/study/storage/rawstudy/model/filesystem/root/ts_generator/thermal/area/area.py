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

from antarest.study.storage.rawstudy.model.filesystem.folder_node import FolderNode
from antarest.study.storage.rawstudy.model.filesystem.inode import TREE
from antarest.study.storage.rawstudy.model.filesystem.root.ts_generator.thermal.area.cluster.cluster import (
    TsGeneratorThermalAreaCluster,
)


class TsGeneratorThermalArea(FolderNode):
    @override
    def build(self) -> TREE:
        area_id = self.config.path.name
        children: TREE = {
            cluster_id: TsGeneratorThermalAreaCluster(
                self.matrix_mapper, self.config.next_file(cluster_id), self.config.get_thermal_ids(area_id)
            )
            for cluster_id in self.config.get_thermal_ids(area_id)
        }
        return children
