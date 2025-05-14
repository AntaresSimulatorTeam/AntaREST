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


class InputThermalAreasIni(IniFileNode):
    def __init__(self, config: FileStudyTreeConfig):
        section = {a: float for a in config.area_names()}
        types = {"unserverdenergycost": section, "spilledenergycost": {}}
        IniFileNode.__init__(self, config, types)
