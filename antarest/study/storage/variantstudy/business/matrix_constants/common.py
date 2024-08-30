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

from typing import List

from antarest.matrixstore.model import MatrixData

NULL_MATRIX: List[List[MatrixData]] = [[]]
NULL_SCENARIO_MATRIX: List[List[MatrixData]] = [[0.0]] * 8760
FIXED_4_COLUMNS = [[0.0, 0.0, 0.0, 0.0]] * 8760
FIXED_8_COLUMNS = [[0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]] * 8760
