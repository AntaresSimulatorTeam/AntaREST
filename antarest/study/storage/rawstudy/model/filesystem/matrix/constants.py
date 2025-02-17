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

import numpy as np

default_scenario_hourly = np.zeros((8760, 1), dtype=np.float64)
default_scenario_hourly.flags.writeable = False

default_scenario_hourly_ones = np.ones((8760, 1), dtype=np.float64)
default_scenario_hourly_ones.flags.writeable = False

default_scenario_daily = np.zeros((365, 1), dtype=np.float64)
default_scenario_daily.flags.writeable = False

default_scenario_daily_ones = np.ones((365, 1), dtype=np.float64)
default_scenario_daily_ones.flags.writeable = False

default_scenario_monthly = np.zeros((12, 1), dtype=np.float64)
default_scenario_monthly.flags.writeable = False

default_4_fixed_hourly = np.zeros((8760, 4), dtype=np.float64)
default_4_fixed_hourly.flags.writeable = False

default_6_fixed_hourly = np.zeros((8760, 6), dtype=np.float64)
default_6_fixed_hourly.flags.writeable = False

default_8_fixed_hourly = np.zeros((8760, 8), dtype=np.float64)
default_8_fixed_hourly.flags.writeable = False
