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

pmax_injection = np.ones((8760, 1), dtype=np.float64)
pmax_injection.flags.writeable = False

pmax_withdrawal = np.ones((8760, 1), dtype=np.float64)
pmax_withdrawal.flags.writeable = False

inflows = np.zeros((8760, 1), dtype=np.float64)
inflows.flags.writeable = False

lower_rule_curve = np.zeros((8760, 1), dtype=np.float64)
lower_rule_curve.flags.writeable = False

upper_rule_curve = np.ones((8760, 1), dtype=np.float64)
upper_rule_curve.flags.writeable = False

costs = np.zeros((8760, 1), dtype=np.float64)
costs.flags.writeable = False
