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
import { STORAGE_GROUPS } from "./constants";

export const storageGroupSchema = z.enum(STORAGE_GROUPS);

export const storageSchema = z.object({
  id: z.string(),
  name: z.string(),
  // Before v9.2, `group` was restricted to the predefined groups (see `storageGroupSchema`).
  // Since v9.2, it can be any custom string.
  group: z.string(),
  injectionNominalCapacity: z.number().min(0),
  withdrawalNominalCapacity: z.number().min(0),
  reservoirCapacity: z.number().min(0),
  efficiency: z.number().min(0),
  initialLevel: z.number().min(0).max(1),
  initialLevelOptim: z.boolean(),
  // Version-specific fields may be missing or `null` for older studies.
  // `nullishToOptional` normalizes `null` to `undefined`.
  // Since v8.8
  enabled: nullishToOptional(z.boolean()).optional(),
  // Since v9.2
  efficiencyWithdrawal: nullishToOptional(z.number().min(0)).optional(),
  penalizeVariationInjection: nullishToOptional(z.boolean()).optional(),
  penalizeVariationWithdrawal: nullishToOptional(z.boolean()).optional(),
  // Since v9.3
  allowOverflow: nullishToOptional(z.boolean()).optional(),
});

export const storagesSchema = z.array(storageSchema);

export const storageCreationSchema = storageSchema
  .omit({ id: true })
  .partial()
  .required({ name: true });

export const storageUpdateSchema = storageSchema.omit({ id: true, name: true }).partial();
