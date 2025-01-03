# Copyright (c) 2024, RTE (https://www.rte-france.com)
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

from antarest.study.storage.rawstudy.model.filesystem.common.prepro import PreproCorrelation
from antarest.study.storage.rawstudy.model.filesystem.folder_node import FolderNode
from antarest.study.storage.rawstudy.model.filesystem.inode import TREE
from antarest.study.storage.rawstudy.model.filesystem.root.input.hydro.prepro.area.area import InputHydroPreproArea


class InputHydroPrepro(FolderNode):
    @override
    def build(self) -> TREE:
        children: TREE = {
            a: InputHydroPreproArea(self.context, self.config.next_file(a)) for a in self.config.area_names()
        }
        children["correlation"] = PreproCorrelation(self.context, self.config.next_file("correlation.ini"))
        return children
