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
from antarest.study.storage.rawstudy.model.filesystem.root.input.hydro.allocation.allocation import InputHydroAllocation
from antarest.study.storage.rawstudy.model.filesystem.root.input.hydro.common.common import InputHydroCommon
from antarest.study.storage.rawstudy.model.filesystem.root.input.hydro.hydro_ini import InputHydroIni
from antarest.study.storage.rawstudy.model.filesystem.root.input.hydro.prepro.prepro import InputHydroPrepro
from antarest.study.storage.rawstudy.model.filesystem.root.input.hydro.series.series import InputHydroSeries


class InputHydro(FolderNode):
    @override
    def build(self) -> TREE:
        children: TREE = {
            "allocation": InputHydroAllocation(self.matrix_mapper, self.config.next_file("allocation")),
            "common": InputHydroCommon(self.matrix_mapper, self.config.next_file("common")),
            "prepro": InputHydroPrepro(self.matrix_mapper, self.config.next_file("prepro")),
            "series": InputHydroSeries(self.matrix_mapper, self.config.next_file("series")),
            "hydro": InputHydroIni(self.config.next_file("hydro.ini")),
        }
        return children
