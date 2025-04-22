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

from antarest.core.serde.ini_common import any_section_option_matcher
from antarest.core.serde.ini_reader import LOWER_CASE_PARSER, IniReader
from antarest.core.serde.ini_writer import LOWER_CASE_SERIALIZER, IniWriter
from antarest.matrixstore.uri_resolver_service import UriResolverService
from antarest.study.storage.rawstudy.model.filesystem.config.model import FileStudyTreeConfig
from antarest.study.storage.rawstudy.model.filesystem.folder_node import FolderNode
from antarest.study.storage.rawstudy.model.filesystem.ini_file_node import IniFileNode
from antarest.study.storage.rawstudy.model.filesystem.inode import TREE

_VALUE_PARSERS = {any_section_option_matcher("group"): LOWER_CASE_PARSER}
_VALUE_SERIALIZERS = {any_section_option_matcher("group"): LOWER_CASE_SERIALIZER}


class ClusteredRenewableClusterConfig(IniFileNode):
    def __init__(
        self,
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
        IniFileNode.__init__(
            self,
            config,
            types,
            reader=IniReader(value_parsers=_VALUE_PARSERS),
            writer=IniWriter(value_serializers=_VALUE_SERIALIZERS),
        )


class ClusteredRenewableCluster(FolderNode):
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
        return {"list": ClusteredRenewableClusterConfig(self.config.next_file("list.ini"), self.area)}


class ClusteredRenewableAreaCluster(FolderNode):
    @override
    def build(self) -> TREE:
        return {
            area: ClusteredRenewableCluster(self.context, self.config.next_file(area), area)
            for area in self.config.area_names()
        }
