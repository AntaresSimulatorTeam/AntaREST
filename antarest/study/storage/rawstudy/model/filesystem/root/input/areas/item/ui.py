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


class InputAreasUi(IniFileNode):
    """
    Examples
    --------
    [ui]
    x = 1
    y = 135
    color_r = 0
    color_g = 128
    color_b = 255
    layers = 0
    [layerX]
    0 = 1

    [layerY]
    0 = 135

    [layerColor]
    0 = 0 , 128 , 255
    """

    def __init__(self, config: FileStudyTreeConfig):
        types = {
            "ui": {
                "x": int,
                "y": int,
                "color_r": int,
                "color_g": int,
                "color_b": int,
                "layers": int,
            },
            "layerX": {"0": int},
            "layerY": {"0": int},
            "layerColor": {"0": str},
        }
        IniFileNode.__init__(self, config, types)
