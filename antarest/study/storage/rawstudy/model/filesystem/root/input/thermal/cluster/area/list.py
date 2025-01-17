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
from antarest.study.storage.rawstudy.model.filesystem.ini_file_node import IniFileNode


class InputThermalClustersAreaList(IniFileNode):
    def __init__(
        self,
        context: ContextServer,
        config: FileStudyTreeConfig,
        area: str,
    ):
        section = {
            "name": str,
            "group": str,
            "unitcount": int,
            "nominalcapacity": float,
            "market-bid-cost": float,
        }
        types = {th: section for th in config.get_thermal_ids(area)}
        super().__init__(context, config, types)

    @override
    def get(
        self, url: t.Optional[t.List[str]] = None, depth: int = -1, expanded: bool = False, formatted: bool = True
    ) -> SUB_JSON:
        return super()._get_lowered_content(url, depth, expanded)

    @override
    def save(self, data: SUB_JSON, url: t.Optional[t.List[str]] = None) -> None:
        super().save_lowered_content(data, url or [])
