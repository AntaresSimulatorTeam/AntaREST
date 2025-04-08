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


import pandas as pd

NULL_MATRIX = pd.DataFrame()
NULL_SCENARIO_MATRIX = pd.DataFrame([[0]] * 8760)
FIXED_4_COLUMNS = pd.DataFrame([[0, 0, 0, 0]] * 8760)
FIXED_8_COLUMNS = pd.DataFrame([[0, 0, 0, 0, 0, 0, 0, 0]] * 8760)
