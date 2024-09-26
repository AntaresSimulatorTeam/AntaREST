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

from typing import Any, Dict

from antarest.study.model import STUDY_VERSION_650, STUDY_VERSION_860
from antarest.study.storage.rawstudy.model.filesystem.folder_node import FolderNode
from antarest.study.storage.rawstudy.model.filesystem.inode import TREE, INode
from antarest.study.storage.rawstudy.model.filesystem.matrix.constants import (
    default_scenario_daily,
    default_scenario_hourly,
    default_scenario_monthly,
)
from antarest.study.storage.rawstudy.model.filesystem.matrix.input_series_matrix import InputSeriesMatrix
from antarest.study.storage.rawstudy.model.filesystem.matrix.matrix import MatrixFrequency


class InputHydroSeriesArea(FolderNode):
    def build(self) -> TREE:
        study_version = self.config.version
        freq = MatrixFrequency.DAILY if study_version >= STUDY_VERSION_650 else MatrixFrequency.MONTHLY
        default_empty = default_scenario_daily if study_version >= STUDY_VERSION_650 else default_scenario_monthly
        hydro_series_matrices: Dict[str, INode[Any, Any, Any]] = {
            "mod": InputSeriesMatrix(
                self.context,
                self.config.next_file("mod.txt"),
                freq=freq,
                default_empty=default_empty,
            ),
            # Run of River
            "ror": InputSeriesMatrix(
                self.context,
                self.config.next_file("ror.txt"),
                freq=MatrixFrequency.HOURLY,
                default_empty=default_scenario_hourly,
            ),
        }
        if study_version >= STUDY_VERSION_860:
            hydro_series_matrices["mingen"] = InputSeriesMatrix(
                self.context,
                self.config.next_file("mingen.txt"),
                freq=MatrixFrequency.HOURLY,
                default_empty=default_scenario_hourly,
            )
        return hydro_series_matrices
