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

from antarest.study.storage.rawstudy.model.filesystem.config.model import FileStudyTreeConfig
from antarest.study.storage.rawstudy.model.filesystem.ini_file_node import IniFileNode


class InputAreasOptimization(IniFileNode):
    """
    Examples
    --------

    [nodal optimization]
    non-dispatchable-power = true
    dispatchable-hydro-power = true
    other-dispatchable-power = true
    spread-unsupplied-energy-cost = 0.000000
    spread-spilled-energy-cost = 0.000000

    [filtering]
    filter-synthesis = daily, monthly
    filter-year-by-year = hourly, weekly, annual
    """

    def __init__(self, config: FileStudyTreeConfig):
        types = {
            "nodal optimization": {
                "non-dispatchable-power": bool,
                "dispatchable-hydro-power": bool,
                "other-dispatchable-power": bool,
                "spread-unsupplied-energy-cost": (int, float),
                "spread-spilled-energy-cost": (int, float),
            },
            "filtering": {"filter-synthesis": str, "filter-year-by-year": str},
        }
        IniFileNode.__init__(self, config, types)
