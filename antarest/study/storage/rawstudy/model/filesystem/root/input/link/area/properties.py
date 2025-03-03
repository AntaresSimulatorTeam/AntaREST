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

from antarest.study.model import STUDY_VERSION_6_5
from antarest.study.storage.rawstudy.model.filesystem.config.model import FileStudyTreeConfig
from antarest.study.storage.rawstudy.model.filesystem.ini_file_node import IniFileNode


class InputLinkAreaProperties(IniFileNode):
    def __init__(
        self,
        config: FileStudyTreeConfig,
        area: str,
    ):
        section = {
            "hurdles-cost": bool,
            "transmission-capacities": str,
            "display-comments": bool,
            "filter-synthesis": str,
            "filter-year-by-year": str,
        }

        if config.version >= STUDY_VERSION_6_5:
            section["loop-flow"] = bool
            section["use-phase-shifter"] = bool
            section["asset-type"] = str
            section["link-style"] = str
            section["link-width"] = int
            section["colorr"] = int
            section["colorg"] = int
            section["colorb"] = int

        types = {link: section for link in config.get_links(area)}
        IniFileNode.__init__(self, config, types)
