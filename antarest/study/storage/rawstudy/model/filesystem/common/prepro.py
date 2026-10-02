# Copyright (c) 2026, RTE (https://www.rte-france.com)
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

from antarest.study.storage.rawstudy.model.filesystem.config.model import FileStudyTreeConfig
from antarest.study.storage.rawstudy.model.filesystem.folder_node import FolderNode
from antarest.study.storage.rawstudy.model.filesystem.ini_file_node import IniFileNode
from antarest.study.storage.rawstudy.model.filesystem.inode import TREE
from antarest.study.storage.rawstudy.model.filesystem.matrix.input_series_matrix import InputSeriesMatrix
from antarest.study.storage.rawstudy.model.filesystem.matrix.simulator_default import (
    default_conversion,
    default_data,
    default_k,
    default_scenario_hourly,
)


class PreproCorrelation(IniFileNode):
    def __init__(self, config: FileStudyTreeConfig):
        IniFileNode.__init__(self, config)


class PreproAreaSettings(IniFileNode):
    def __init__(self, config: FileStudyTreeConfig):
        IniFileNode.__init__(self, config)


class PreproArea(FolderNode):
    @override
    def build(self) -> TREE:
        children: TREE = {
            "conversion": InputSeriesMatrix(
                self.matrix_storage_context, self.config.next_file("conversion.txt"), default_empty=default_conversion
            ),
            "data": InputSeriesMatrix(
                self.matrix_storage_context, self.config.next_file("data.txt"), default_empty=default_data
            ),
            "k": InputSeriesMatrix(
                self.matrix_storage_context, self.config.next_file("k.txt"), default_empty=default_k
            ),
            "translation": InputSeriesMatrix(
                self.matrix_storage_context,
                self.config.next_file("translation.txt"),
                default_empty=default_scenario_hourly,
            ),
            "settings": PreproAreaSettings(self.config.next_file("settings.ini")),
        }
        return children


class InputPrepro(FolderNode):
    @override
    def build(self) -> TREE:
        children: TREE = {
            a: PreproArea(self.matrix_storage_context, self.config.next_file(a)) for a in self.config.area_names()
        }
        children["correlation"] = PreproCorrelation(self.config.next_file("correlation.ini"))
        return children
