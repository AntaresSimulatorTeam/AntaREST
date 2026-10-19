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

import { thermalClusterSchema } from "@/services/api/studies/areas/thermals/schemas";

export const cluster = thermalClusterSchema.parse({
  id: "gas",
  name: "Gas",
  group: null,
  enabled: true,
  unitCount: 2,
  nominalCapacity: 100,
  mustRun: false,
  minStablePower: 10,
  spinning: 0,
  minUpTime: 1,
  minDownTime: 1,
  marginalCost: 20,
  fixedCost: 0,
  startupCost: 0,
  marketBidCost: 20,
  spreadCost: 0,
  genTs: "use global",
  volatilityForced: 0,
  volatilityPlanned: 0,
  lawForced: "uniform",
  lawPlanned: "uniform",
  co2: 0,
  so2: 0,
  nh3: 0,
  nox: 0,
  nmvoc: 0,
  pm25: 0,
  pm5: 0,
  pm10: 0,
  op1: 0,
  op2: 0,
  op3: 0,
  op4: 0,
  op5: 0,
  costGeneration: "SetManually",
  efficiency: 100,
  variableOMCost: 0,
});
