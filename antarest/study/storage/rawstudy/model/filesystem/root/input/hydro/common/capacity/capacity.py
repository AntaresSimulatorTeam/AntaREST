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
import numpy.typing as npt
from antares.study.version import StudyVersion
from typing_extensions import override

from antarest.study.model import STUDY_VERSION_6_5, MatrixFrequency
from antarest.study.storage.rawstudy.model.filesystem.folder_node import FolderNode
from antarest.study.storage.rawstudy.model.filesystem.inode import TREE
from antarest.study.storage.rawstudy.model.filesystem.matrix.constants import (
    default_credit_modulation,
    default_maxpower,
    default_reservoir,
    default_scenario_daily,
    default_water_values,
)
from antarest.study.storage.rawstudy.model.filesystem.matrix.input_series_matrix import InputSeriesMatrix


class MatrixInfo(TypedDict, total=False):
    name: str
    freq: MatrixFrequency
    start_version: StudyVersion
    default_empty: Callable[[], npt.NDArray[np.float64]]


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
        "default_empty": default_scenario_daily,
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
