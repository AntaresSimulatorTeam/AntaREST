# Copyright (c) 2024, RTE (https://www.rte-france.com)
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

from typing import List, TypedDict

from antares.study.version import StudyVersion

from antarest.study.storage.rawstudy.model.filesystem.folder_node import FolderNode
from antarest.study.storage.rawstudy.model.filesystem.inode import TREE
from antarest.study.storage.rawstudy.model.filesystem.matrix.input_series_matrix import InputSeriesMatrix
from antarest.study.storage.rawstudy.model.filesystem.matrix.matrix import MatrixFrequency


class MatrixInfo(TypedDict, total=False):
    name: str
    freq: MatrixFrequency
    start_version: StudyVersion


INITIAL_VERSION = StudyVersion.parse(0)
VERSION_650 = StudyVersion.parse(650)
# noinspection SpellCheckingInspection
MATRICES_INFO: List[MatrixInfo] = [
    {
        "name": "maxpower",
        "freq": MatrixFrequency.DAILY,
        "start_version": INITIAL_VERSION,
    },
    {
        "name": "reservoir",
        "freq": MatrixFrequency.DAILY,
        "start_version": INITIAL_VERSION,
    },
    {
        "name": "inflowPattern",
        "freq": MatrixFrequency.DAILY,
        "start_version": VERSION_650,
    },
    {
        "name": "creditmodulations",
        "freq": MatrixFrequency.HOURLY,
        "start_version": VERSION_650,
    },
    {
        "name": "waterValues",
        "freq": MatrixFrequency.DAILY,
        "start_version": VERSION_650,
    },
]


class InputHydroCommonCapacity(FolderNode):
    def build(self) -> TREE:
        children: TREE = {}
        for info in MATRICES_INFO:
            if self.config.version >= info["start_version"]:
                for area in self.config.area_names():
                    name = f"{info['name']}_{area}"
                    children[name] = InputSeriesMatrix(
                        self.context,
                        self.config.next_file(f"{name}.txt"),
                        freq=info["freq"],
                    )
        return children
