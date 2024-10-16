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

from antarest.study.storage.rawstudy.model.filesystem.config.model import FileStudyTreeConfig
from antarest.study.storage.rawstudy.model.filesystem.context import ContextServer
from antarest.study.storage.rawstudy.model.filesystem.folder_node import FolderNode
from antarest.study.storage.rawstudy.model.filesystem.ini_file_node import IniFileNode
from antarest.study.storage.rawstudy.model.filesystem.inode import TREE


class ClusteredRenewableClusterConfig(IniFileNode):
    def __init__(
        self,
        context: ContextServer,
        config: FileStudyTreeConfig,
        area: str,
    ):
        section = {
            "name": str,
            "group": str,
            "enabled": bool,
            "unitcount": int,
            "nomialcapacity": 0,
            "ts-interpretation": str,
        }
        types = {cluster_id: section for cluster_id in config.get_renewable_ids(area)}
        IniFileNode.__init__(self, context, config, types)


class ClusteredRenewableCluster(FolderNode):
    def __init__(
        self,
        context: ContextServer,
        config: FileStudyTreeConfig,
        area: str,
    ):
        super().__init__(context, config)
        self.area = area

    def build(self) -> TREE:
        return {"list": ClusteredRenewableClusterConfig(self.context, self.config.next_file("list.ini"), self.area)}


class ClusteredRenewableAreaCluster(FolderNode):
    def build(self) -> TREE:
        return {
            area: ClusteredRenewableCluster(self.context, self.config.next_file(area), area)
            for area in self.config.area_names()
        }
