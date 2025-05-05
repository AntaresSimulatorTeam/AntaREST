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
from antarest.study.storage.rawstudy.model.filesystem.raw_file_node import RawFileNode
from antarest.study.storage.rawstudy.model.filesystem.root.output.simulation.about.study import (
    OutputSimulationAboutStudy,
)
from antarest.study.storage.rawstudy.model.filesystem.root.settings.generaldata import GeneralData


class OutputSimulationAbout(FolderNode):
    @override
    def build(self) -> TREE:
        children: TREE = {
            "areas": RawFileNode(self.matrix_mapper, self.config.next_file("areas.txt")),
            "comments": RawFileNode(self.matrix_mapper, self.config.next_file("comments.txt")),
            "links": RawFileNode(self.matrix_mapper, self.config.next_file("links.txt")),
            # TODO "map": OutputSimulationAboutMap(self.context, self.config.next_file("map")),
            "study": OutputSimulationAboutStudy(self.config.next_file("study.ini")),
            "parameters": GeneralData(self.config.next_file("parameters.ini")),
        }
        return children
