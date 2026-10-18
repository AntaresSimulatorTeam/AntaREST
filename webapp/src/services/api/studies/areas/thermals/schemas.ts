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

import { nameToId } from "@/services/utils";
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
  // Backend models preserve name casing, while database storage lowercases IDs.
  // TODO: Remove normalization once the backend returns consistent IDs.
  id: z.string().transform(nameToId),
  name: z.string(),
  // Before v9.3, `group` was restricted to the predefined groups (see `thermalGroupSchema`).
  // Since v9.3, it can be any custom string.
  group: z.string(),
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
  // Version-specific fields may be missing or `null` for older studies.
  // `nullishToOptional` normalizes `null` to `undefined`.
  // Since v8.6
  so2: nullishToOptional(z.number()).optional(),
  nh3: nullishToOptional(z.number()).optional(),
  nox: nullishToOptional(z.number()).optional(),
  nmvoc: nullishToOptional(z.number()).optional(),
  pm25: nullishToOptional(z.number()).optional(),
  pm5: nullishToOptional(z.number()).optional(),
  pm10: nullishToOptional(z.number()).optional(),
  op1: nullishToOptional(z.number()).optional(),
  op2: nullishToOptional(z.number()).optional(),
  op3: nullishToOptional(z.number()).optional(),
  op4: nullishToOptional(z.number()).optional(),
  op5: nullishToOptional(z.number()).optional(),
  // Since v8.7
  costGeneration: nullishToOptional(z.enum(COST_GENERATION_OPTIONS)).optional(),
  efficiency: nullishToOptional(z.number()).optional(),
  variableOMCost: nullishToOptional(z.number()).optional(),
});

export const thermalClustersSchema = z.array(thermalClusterSchema);

export const thermalClusterCreationSchema = thermalClusterSchema
  .omit({ id: true })
  .partial()
  .required({ name: true });

export const thermalClusterUpdateSchema = thermalClusterSchema
  .omit({ id: true, name: true })
  .partial();
