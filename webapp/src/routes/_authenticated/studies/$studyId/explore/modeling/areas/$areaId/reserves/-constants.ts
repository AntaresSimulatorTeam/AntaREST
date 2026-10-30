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

import type { ReserveCreation } from "@/services/api/studies/areas/reserves/types";

export const DEFAULT_RESERVE_VALUES = {
  name: "",
  type: "up",
  failureCost: 0,
  spillageCost: 0,
  referenceActivationDuration: 0,
  powerActivationRatio: 0,
  energyActivationRatio: 0,
} as const satisfies ReserveCreation;
