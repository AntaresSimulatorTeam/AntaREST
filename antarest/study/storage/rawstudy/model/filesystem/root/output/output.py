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

from antarest.study.storage.rawstudy.model.filesystem.bucket_node import BucketNode
from antarest.study.storage.rawstudy.model.filesystem.folder_node import FolderNode
from antarest.study.storage.rawstudy.model.filesystem.inode import TREE
from antarest.study.storage.rawstudy.model.filesystem.root.output.simulation.simulation import OutputSimulation


class Output(FolderNode):
    @override
    def build(self) -> TREE:
        children: TREE = {
            str(s.get_file()): OutputSimulation(
                self.matrix_mapper,
                self.config.next_file(s.get_file(), is_output=True),
                s,
            )
            for i, s in self.config.outputs.items()
        }

        if (self.config.path / "logs").exists():
            children["logs"] = BucketNode(self.matrix_mapper, self.config.next_file("logs"))
        return children

    @override
    def normalize(self) -> None:
        pass  # no external store in this node

    @override
    def denormalize(self) -> None:
        pass  # no external store in this node
