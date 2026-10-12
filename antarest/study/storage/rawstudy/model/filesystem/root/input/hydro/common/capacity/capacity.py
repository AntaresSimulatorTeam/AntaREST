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
from typing import TypedDict

import numpy as np
import numpy.typing as npt
from antares.study.version import StudyVersion
from typing_extensions import override

from antarest.core.serde.ini_reader import IniReader
from antarest.study.business.model.config.compatibility_parameters_model import HydroPmax
from antarest.study.model import STUDY_VERSION_6_5, STUDY_VERSION_9_2
from antarest.study.storage.rawstudy.model.filesystem.config.compatibility_parameters import (
    parse_compatibility_parameters,
)
from antarest.study.storage.rawstudy.model.filesystem.folder_node import FolderNode
from antarest.study.storage.rawstudy.model.filesystem.inode import TREE
from antarest.study.storage.rawstudy.model.filesystem.matrix.input_series_matrix import InputSeriesMatrix
from antarest.study.storage.rawstudy.model.filesystem.matrix.simulator_default import (
    default_credit_modulation,
    default_maxpower,
    default_reservoir,
    default_scenario_daily,
    default_water_values,
)


class MatrixInfo(TypedDict, total=False):
    name: str
    start_version: StudyVersion
    default_empty: Callable[[], npt.NDArray[np.float64]]
    should_exist: bool


INITIAL_VERSION = StudyVersion.parse(0)
# noinspection SpellCheckingInspection
MATRICES_INFO: list[MatrixInfo] = [
    {
        "name": "maxpower",
        "start_version": INITIAL_VERSION,
        "default_empty": default_maxpower,
    },
    {
        "name": "reservoir",
        "start_version": INITIAL_VERSION,
        "default_empty": default_reservoir,
    },
    {
        "name": "inflowPattern",
        "start_version": STUDY_VERSION_6_5,
        "default_empty": default_scenario_daily,
    },
    {
        "name": "creditmodulations",
        "start_version": STUDY_VERSION_6_5,
        "default_empty": default_credit_modulation,
    },
    {
        "name": "waterValues",
        "start_version": STUDY_VERSION_6_5,
        "default_empty": default_water_values,
    },
    {
        "name": "maxDailyGenEnergy",
        "start_version": STUDY_VERSION_9_2,
        "default_empty": default_scenario_daily,
        "should_exist": False,
    },
    {
        "name": "maxDailyPumpEnergy",
        "start_version": STUDY_VERSION_9_2,
        "default_empty": default_scenario_daily,
        "should_exist": False,
    },
]


class InputHydroCommonCapacity(FolderNode):
    @override
    def build(self) -> TREE:
        hourly_pmax = False
        if self.config.version >= STUDY_VERSION_9_2:
            general_data = IniReader().read(
                self.config.study_path / "settings/generaldata.ini", section="compatibility", option="hydro-pmax"
            )
            hourly_pmax = parse_compatibility_parameters(general_data).hydro_pmax == HydroPmax.HOURLY

        children: TREE = {}
        for info in MATRICES_INFO:
            if self.config.version >= info["start_version"]:
                for area in self.config.area_names():
                    name = f"{info['name']}_{area}"
                    # Only hourly hydro power series replace the legacy maxpower file.
                    optional_maxpower = info["name"] == "maxpower" and hourly_pmax
                    children[name] = InputSeriesMatrix(
                        self.matrix_storage_context,
                        self.config.next_file(f"{name}.txt"),
                        default_empty=info["default_empty"],
                        should_exist=info.get("should_exist", True) and not optional_maxpower,
                    )
        return children
