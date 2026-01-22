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

"""
These matrices are the default Simulator ones.
We show them in the IHM when the matrix file is empty.
"""


def default_scenario_hourly() -> np.ndarray:
    return np.zeros((8760, 1), dtype=np.float64)


def default_scenario_hourly_ones() -> np.ndarray:
    return np.ones((8760, 1), dtype=np.float64)


def default_scenario_daily() -> np.ndarray:
    return np.zeros((365, 1), dtype=np.float64)


def default_scenario_monthly() -> np.ndarray:
    return np.zeros((12, 1), dtype=np.float64)


def default_4_fixed_hourly() -> np.ndarray:
    return np.zeros((8760, 4), dtype=np.float64)


def default_6_fixed_hourly() -> np.ndarray:
    return np.zeros((8760, 6), dtype=np.float64)


def default_8_fixed_hourly() -> np.ndarray:
    return np.zeros((8760, 8), dtype=np.float64)


def default_k() -> np.ndarray:
    return np.zeros((24, 12), dtype=np.float64)


def default_conversion() -> np.ndarray:
    return np.zeros((2, 3), dtype=np.float64)


def default_data() -> np.ndarray:
    return np.zeros((12, 6), dtype=np.float64)


def default_maxpower() -> np.ndarray:
    return np.zeros((365, 4), dtype=np.float64)


def default_reservoir() -> np.ndarray:
    return np.zeros((365, 3), dtype=np.float64)


def default_credit_modulation() -> np.ndarray:
    return np.zeros((2, 101), dtype=np.float64)


def default_water_values() -> np.ndarray:
    return np.zeros((365, 101), dtype=np.float64)


def default_energy() -> np.ndarray:
    return np.zeros((12, 5), dtype=np.float64)


def default_cost_level() -> np.ndarray:
    return np.full((8760, 1), -1e-6)
