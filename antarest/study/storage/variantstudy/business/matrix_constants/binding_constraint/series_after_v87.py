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

import numpy as np


def default_bc_hourly() -> np.ndarray:
    return np.zeros((8784, 1), dtype=np.float64)


def default_bc_weekly_daily() -> np.ndarray:
    return np.zeros((366, 1), dtype=np.float64)
