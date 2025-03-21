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

from antarest.study.model import STUDY_VERSION_9_2
from antarest.study.storage.rawstudy.model.filesystem.folder_node import FolderNode
from antarest.study.storage.rawstudy.model.filesystem.inode import TREE
from antarest.study.storage.rawstudy.model.filesystem.matrix.input_series_matrix import InputSeriesMatrix
from antarest.study.storage.rawstudy.model.filesystem.root.input.st_storage.clusters.clusters import (
    InputSTStorageClusters,
)
from antarest.study.storage.rawstudy.model.filesystem.root.input.st_storage.series.series import InputSTStorageSeries


class InputSTStorage(FolderNode):
    # Short-term storage objects are introduced in the v8.6 of AntaresSimulator.
    # This new object simplifies the previously complex modeling of short-term storage such as batteries or STEPs.

    @override
    def build(self) -> TREE:
        children: TREE = {
            "clusters": InputSTStorageClusters(self.context, self.config.next_file("clusters")),
            "series": InputSTStorageSeries(self.context, self.config.next_file("series")),
        }

        if self.config.version >= STUDY_VERSION_9_2:
            children["cost_injection"] = InputSeriesMatrix(self.context, self.config.next_file("cost-injection.txt"))
            children["cost_withdrawal"] = InputSeriesMatrix(self.context, self.config.next_file("cost-withdrawal.txt"))
            children["cost_level"] = InputSeriesMatrix(self.context, self.config.next_file("cost-level.txt"))
            children["cost_variation_injection"] = InputSeriesMatrix(
                self.context, self.config.next_file("cost-variation-injection.txt")
            )
            children["cost_variation_withdrawal"] = InputSeriesMatrix(
                self.context, self.config.next_file("cost-variation-withdrawal.txt")
            )

        return children
