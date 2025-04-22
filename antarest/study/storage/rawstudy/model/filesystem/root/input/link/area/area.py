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
import numpy as np
from typing_extensions import override

from antarest.matrixstore.uri_resolver_service import UriResolverService
from antarest.study.model import STUDY_VERSION_8_2
from antarest.study.storage.rawstudy.model.filesystem.config.model import FileStudyTreeConfig
from antarest.study.storage.rawstudy.model.filesystem.folder_node import FolderNode
from antarest.study.storage.rawstudy.model.filesystem.inode import TREE
from antarest.study.storage.rawstudy.model.filesystem.matrix.constants import default_6_fixed_hourly
from antarest.study.storage.rawstudy.model.filesystem.matrix.input_series_matrix import InputSeriesMatrix
from antarest.study.storage.rawstudy.model.filesystem.root.input.link.area.capacities.capacities import (
    InputLinkAreaCapacities,
)
from antarest.study.storage.rawstudy.model.filesystem.root.input.link.area.properties import InputLinkAreaProperties

default_link_legacy_matrix = np.zeros((8760, 8), dtype=np.float64)
default_link_legacy_matrix[:, :2] = 1
default_link_legacy_matrix.flags.writeable = False


class InputLinkArea(FolderNode):
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
        children: TREE
        ctx = self.context
        cfg = self.config
        if cfg.version < STUDY_VERSION_8_2:
            children = {
                link: InputSeriesMatrix(ctx, cfg.next_file(f"{link}.txt"), default_empty=default_link_legacy_matrix)
                for link in cfg.get_links(self.area)
            }
        else:
            children = {
                f"{link}_parameters": InputSeriesMatrix(
                    ctx, cfg.next_file(f"{link}_parameters.txt"), default_empty=default_6_fixed_hourly
                )
                for link in cfg.get_links(self.area)
            }
            children["capacities"] = InputLinkAreaCapacities(ctx, cfg.next_file("capacities"), area=self.area)

        children["properties"] = InputLinkAreaProperties(
            cfg.next_file("properties.ini"),
            area=self.area,
        )

        return children
