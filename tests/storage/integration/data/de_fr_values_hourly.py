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

import numpy

de_fr_values_hourly = {
    "columns": [
        ("FLOW LIN.", "MWh", ""),
        ("UCAP LIN.", "MWh", ""),
        ("LOOP FLOW", "MWh", ""),
        ("FLOW QUAD.", "MWh", ""),
        ("CONG. FEE (ALG.)", "Euro", ""),
        ("CONG. FEE (ABS.)", "Euro", ""),
        ("MARG. COST", "Euro/MW", ""),
        ("CONG. PROB +", "%", ""),
        ("CONG. PROB -", "%", ""),
        ("HURDLE COST", "Euro", ""),
    ],
    "data": numpy.zeros((168, 10)),
}
