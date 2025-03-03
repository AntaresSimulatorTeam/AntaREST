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

from typing import List, TypedDict

import numpy as np
import numpy.typing as npt
from antares.study.version import StudyVersion
from typing_extensions import override

from antarest.study.model import STUDY_VERSION_6_5
from antarest.study.storage.rawstudy.model.filesystem.folder_node import FolderNode
from antarest.study.storage.rawstudy.model.filesystem.inode import TREE
from antarest.study.storage.rawstudy.model.filesystem.matrix.constants import default_scenario_daily_ones
from antarest.study.storage.rawstudy.model.filesystem.matrix.input_series_matrix import InputSeriesMatrix
from antarest.study.storage.rawstudy.model.filesystem.matrix.matrix import MatrixFrequency


class MatrixInfo(TypedDict, total=False):
    name: str
    freq: MatrixFrequency
    start_version: StudyVersion
    default_empty: npt.NDArray[np.float64]


default_maxpower = np.zeros((365, 4), dtype=np.float64)
default_maxpower[:, 1] = 24
default_maxpower[:, 3] = 24
default_maxpower.flags.writeable = False

default_reservoir = np.zeros((365, 3), dtype=np.float64)
default_reservoir[:, 1] = 0.5
default_reservoir[:, 2] = 1
default_reservoir.flags.writeable = False

default_credit_modulation = np.ones((2, 100), dtype=np.float64)
default_credit_modulation.flags.writeable = False

default_water_values = np.zeros((365, 101), dtype=np.float64)
default_water_values.flags.writeable = False

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
