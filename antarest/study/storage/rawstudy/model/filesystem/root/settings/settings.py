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
from antarest.study.storage.rawstudy.model.filesystem.root.settings.generaldata import GeneralData
from antarest.study.storage.rawstudy.model.filesystem.root.settings.resources.resources import Resources
from antarest.study.storage.rawstudy.model.filesystem.root.settings.scenariobuilder import ScenarioBuilder
from antarest.study.storage.rawstudy.model.filesystem.root.settings.simulations.simulations import SettingsSimulations


class Settings(FolderNode):
    @override
    def build(self) -> TREE:
        children: TREE = {
            "resources": Resources(self.context, self.config.next_file("resources")),
            "simulations": SettingsSimulations(self.context, self.config.next_file("simulations")),
            "comments": RawFileNode(self.context, self.config.next_file("comments.txt")),
            "generaldata": GeneralData(self.config.next_file("generaldata.ini")),
            "scenariobuilder": ScenarioBuilder(self.config.next_file("scenariobuilder.dat")),
        }
        return children
