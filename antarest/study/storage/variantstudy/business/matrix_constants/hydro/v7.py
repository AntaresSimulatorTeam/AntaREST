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

from typing import List

from antarest.matrixstore.model import MatrixData

credit_modulations: List[List[MatrixData]] = [[1.0] * 101] * 2
inflow_pattern: List[List[MatrixData]] = [[1.0]] * 365
max_power: List[List[MatrixData]] = [[0.0, 24.0, 0.0, 24.0]] * 365
reservoir: List[List[MatrixData]] = [[0.0, 0.5, 1.0]] * 365
