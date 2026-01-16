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


def default_scenario_hourly() -> np.ndarray:
    return np.zeros((8760, 1), dtype=np.float64)


def default_scenario_hourly_ones() -> np.ndarray:
    return np.ones((8760, 1), dtype=np.float64)


def default_scenario_daily() -> np.ndarray:
    return np.zeros((365, 1), dtype=np.float64)


def default_scenario_daily_ones() -> np.ndarray:
    return np.ones((365, 1), dtype=np.float64)


def default_scenario_monthly() -> np.ndarray:
    return np.zeros((12, 1), dtype=np.float64)


def default_4_fixed_hourly() -> np.ndarray:
    return np.zeros((8760, 4), dtype=np.float64)


def default_6_fixed_hourly() -> np.ndarray:
    return np.zeros((8760, 6), dtype=np.float64)


def default_8_fixed_hourly() -> np.ndarray:
    return np.zeros((8760, 8), dtype=np.float64)
