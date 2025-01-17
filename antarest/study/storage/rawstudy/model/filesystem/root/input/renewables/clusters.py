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
import typing as t

from typing_extensions import override

from antarest.core.model import SUB_JSON
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
            "nominalcapacity": float,
            "ts-interpretation": str,
        }
        types = {cluster_id: section for cluster_id in config.get_renewable_ids(area)}
        IniFileNode.__init__(self, context, config, types)

    @override
    def get(
        self, url: t.Optional[t.List[str]] = None, depth: int = -1, expanded: bool = False, formatted: bool = True
    ) -> SUB_JSON:
        return super()._get_lowered_content(url, depth, expanded)

    @override
    def save(self, data: SUB_JSON, url: t.Optional[t.List[str]] = None) -> None:
        super()._save_content_with_lowered_keys(data, url or [])


class ClusteredRenewableCluster(FolderNode):
    def __init__(
        self,
        context: ContextServer,
        config: FileStudyTreeConfig,
        area: str,
    ):
        super().__init__(context, config)
        self.area = area

    @override
    def build(self) -> TREE:
        return {"list": ClusteredRenewableClusterConfig(self.context, self.config.next_file("list.ini"), self.area)}


class ClusteredRenewableAreaCluster(FolderNode):
    @override
    def build(self) -> TREE:
        return {
            area: ClusteredRenewableCluster(self.context, self.config.next_file(area), area)
            for area in self.config.area_names()
        }
