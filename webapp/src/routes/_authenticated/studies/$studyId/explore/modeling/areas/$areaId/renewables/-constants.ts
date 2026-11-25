/**
 * Copyright (c) 2026, RTE (https://www.rte-france.com)
 *
 * See AUTHORS.txt
 *
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/.
 *
 * SPDX-License-Identifier: MPL-2.0
 *
 * This file is part of the Antares project.
 */

import { TS_INTERPRETATION_OPTIONS } from "@/services/api/studies/areas/renewables/constants";
import type { RenewableClusterCreation } from "@/services/api/studies/areas/renewables/types";

export const DEFAULT_RENEWABLE_VALUES = {
  name: "",
  group: "",
  tsInterpretation: TS_INTERPRETATION_OPTIONS[0],
  enabled: false,
  unitCount: 1,
  nominalCapacity: 0,
} as const satisfies RenewableClusterCreation;
