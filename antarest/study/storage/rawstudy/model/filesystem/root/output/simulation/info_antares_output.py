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


class OutputSimulationInfoAntaresOutput(IniFileNode):
    """
    info.antares-output file

    Examples
    --------
    [general]
    version = 700
    name = hello
    mode = Economy
    date = 2020.10.14 - 14:22
    title = 2020.10.14 - 14:22
    timestamp = 1602678140
    """

    def __init__(self, config: FileStudyTreeConfig):
        types = {
            "general": {
                "version": int,
                "name": str,
                "mode": str,
                "date": str,
                "title": str,
                "timestamp": int,
            }
        }

        IniFileNode.__init__(self, config, types=types)
