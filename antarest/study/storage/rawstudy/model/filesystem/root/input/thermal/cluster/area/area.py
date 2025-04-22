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
from antarest.study.storage.rawstudy.model.filesystem.root.input.thermal.cluster.area.list import (
    InputThermalClustersAreaList,
)


class InputThermalClustersArea(FolderNode):
    def __init__(
        self,
        context: UriResolverService,
        config: FileStudyTreeConfig,
        area: str,
    ):
        super().__init__(context, config)
        self.area = area

    @override
    def build(self) -> TREE:
        children: TREE = {"list": InputThermalClustersAreaList(self.config.next_file("list.ini"), self.area)}
        return children
