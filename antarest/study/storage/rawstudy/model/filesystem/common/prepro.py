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

from antarest.study.storage.rawstudy.model.filesystem.config.model import FileStudyTreeConfig
from antarest.study.storage.rawstudy.model.filesystem.folder_node import FolderNode
from antarest.study.storage.rawstudy.model.filesystem.ini_file_node import IniFileNode
from antarest.study.storage.rawstudy.model.filesystem.inode import TREE
from antarest.study.storage.rawstudy.model.filesystem.matrix.constants import default_scenario_hourly
from antarest.study.storage.rawstudy.model.filesystem.matrix.input_series_matrix import InputSeriesMatrix


class PreproCorrelation(IniFileNode):
    def __init__(self, config: FileStudyTreeConfig):
        types = {
            "general": {"mode": str},
            "0": {},
            "1": {},
            "2": {},
            "3": {},
            "4": {},
            "5": {},
            "6": {},
            "7": {},
            "8": {},
            "9": {},
            "10": {},
            "11": {},
        }
        IniFileNode.__init__(self, config, types)


class PreproAreaSettings(IniFileNode):
    def __init__(self, config: FileStudyTreeConfig):
        IniFileNode.__init__(self, config, types={})


default_k = np.zeros((24, 12), dtype=np.float64)
default_k.flags.writeable = False

default_conversion = np.array([[-9999999980506447872, 0, -9999999980506447872], [0, 0, 0]], dtype=np.float64)
default_conversion.flags.writeable = False

default_data = np.ones((12, 6), dtype=np.float64)
default_data[:, 2] = 0
default_data.flags.writeable = False


class PreproArea(FolderNode):
    @override
    def build(self) -> TREE:
        children: TREE = {
            "conversion": InputSeriesMatrix(
                self.matrix_mapper, self.config.next_file("conversion.txt"), default_empty=default_conversion
            ),
            "data": InputSeriesMatrix(
                self.matrix_mapper, self.config.next_file("data.txt"), default_empty=default_data
            ),
            "k": InputSeriesMatrix(self.matrix_mapper, self.config.next_file("k.txt"), default_empty=default_k),
            "translation": InputSeriesMatrix(
                self.matrix_mapper, self.config.next_file("translation.txt"), default_empty=default_scenario_hourly
            ),
            "settings": PreproAreaSettings(self.config.next_file("settings.ini")),
        }
        return children


class InputPrepro(FolderNode):
    @override
    def build(self) -> TREE:
        children: TREE = {a: PreproArea(self.matrix_mapper, self.config.next_file(a)) for a in self.config.area_names()}
        children["correlation"] = PreproCorrelation(self.config.next_file("correlation.ini"))
        return children
