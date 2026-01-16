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
from collections.abc import Callable
from typing import List, TypedDict

import numpy as np
from antares.study.version import StudyVersion
from typing_extensions import override

from antarest.core.serde.np_array import NpArray
from antarest.study.model import STUDY_VERSION_6_5, MatrixFrequency
from antarest.study.storage.rawstudy.model.filesystem.folder_node import FolderNode
from antarest.study.storage.rawstudy.model.filesystem.inode import TREE
from antarest.study.storage.rawstudy.model.filesystem.matrix.constants import default_scenario_daily_ones
from antarest.study.storage.rawstudy.model.filesystem.matrix.input_series_matrix import InputSeriesMatrix


class MatrixInfo(TypedDict, total=False):
    name: str
    freq: MatrixFrequency
    start_version: StudyVersion
    default_empty: Callable[[], NpArray]


def default_maxpower() -> NpArray:
    maxpower = np.zeros((365, 4), dtype=np.float64)
    maxpower[:, 1] = 24
    maxpower[:, 3] = 24
    return maxpower


def default_reservoir() -> NpArray:
    reservoir = np.zeros((365, 3), dtype=np.float64)
    reservoir[:, 1] = 0.5
    reservoir[:, 2] = 1
    return reservoir


def default_credit_modulation() -> NpArray:
    return np.ones((2, 100), dtype=np.float64)


def default_water_values() -> NpArray:
    return np.zeros((365, 101), dtype=np.float64)


INITIAL_VERSION = StudyVersion.parse(0)
# noinspection SpellCheckingInspection
MATRICES_INFO: List[MatrixInfo] = [
    {
        "name": "maxpower",
        "freq": MatrixFrequency.DAILY,
        "start_version": INITIAL_VERSION,
        "default_empty": default_maxpower,
    },
    {
        "name": "reservoir",
        "freq": MatrixFrequency.DAILY,
        "start_version": INITIAL_VERSION,
        "default_empty": default_reservoir,
    },
    {
        "name": "inflowPattern",
        "freq": MatrixFrequency.DAILY,
        "start_version": STUDY_VERSION_6_5,
        "default_empty": default_scenario_daily_ones,
    },
    {
        "name": "creditmodulations",
        "freq": MatrixFrequency.HOURLY,
        "start_version": STUDY_VERSION_6_5,
        "default_empty": default_credit_modulation,
    },
    {
        "name": "waterValues",
        "freq": MatrixFrequency.DAILY,
        "start_version": STUDY_VERSION_6_5,
        "default_empty": default_water_values,
    },
]


class InputHydroCommonCapacity(FolderNode):
    @override
    def build(self) -> TREE:
        children: TREE = {}
        for info in MATRICES_INFO:
            if self.config.version >= info["start_version"]:
                for area in self.config.area_names():
                    name = f"{info['name']}_{area}"
                    children[name] = InputSeriesMatrix(
                        self.matrix_mapper,
                        self.config.next_file(f"{name}.txt"),
                        freq=info["freq"],
                        default_empty=info["default_empty"],
                    )
        return children
