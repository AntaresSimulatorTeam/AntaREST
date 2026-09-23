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

import { nullishToOptional } from "@/utils/zodUtils";
import { z } from "zod";
import {
  COST_GENERATION_OPTIONS,
  THERMAL_GROUPS,
  TS_GENERATION_OPTIONS,
  TS_LAW_OPTIONS,
} from "./constants";

export const thermalGroupSchema = z.enum(THERMAL_GROUPS);

export const thermalClusterSchema = z.object({
  id: z.string(),
  name: z.string(),
  // Since v9.3, groups can be custom strings. The API also permits no group.
  group: z.string().nullable(),
  enabled: z.boolean(),
  unitCount: z.number(),
  nominalCapacity: z.number(),
  mustRun: z.boolean(),
  minStablePower: z.number(),
  spinning: z.number(),
  minUpTime: z.number(),
  minDownTime: z.number(),
  marginalCost: z.number(),
  fixedCost: z.number(),
  startupCost: z.number(),
  marketBidCost: z.number(),
  spreadCost: z.number(),
  genTs: z.enum(TS_GENERATION_OPTIONS),
  volatilityForced: z.number(),
  volatilityPlanned: z.number(),
  lawForced: z.enum(TS_LAW_OPTIONS),
  lawPlanned: z.enum(TS_LAW_OPTIONS),
  co2: z.number(),
  // Since v8.6; older studies may omit these fields or return null.
  so2: nullishToOptional(z.number()),
  nh3: nullishToOptional(z.number()),
  nox: nullishToOptional(z.number()),
  nmvoc: nullishToOptional(z.number()),
  pm25: nullishToOptional(z.number()),
  pm5: nullishToOptional(z.number()),
  pm10: nullishToOptional(z.number()),
  op1: nullishToOptional(z.number()),
  op2: nullishToOptional(z.number()),
  op3: nullishToOptional(z.number()),
  op4: nullishToOptional(z.number()),
  op5: nullishToOptional(z.number()),
  // Since v8.7.
  costGeneration: nullishToOptional(z.enum(COST_GENERATION_OPTIONS)),
  efficiency: nullishToOptional(z.number()),
  variableOMCost: nullishToOptional(z.number()),
});

export const thermalClustersSchema = z.array(thermalClusterSchema);

export const createThermalClusterParamsSchema = thermalClusterSchema
  .omit({ id: true })
  .partial()
  .required({ name: true });

export const updateThermalClusterParamsSchema = thermalClusterSchema
  .omit({ id: true, name: true })
  .partial();
