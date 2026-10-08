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
  // Before v9.2, non-null groups must match storageGroupSchema; custom groups are rejected.
  // Since v9.2, custom groups are accepted. The API permits null and lowercases groups.
  group: z.string().nullable(),
  injectionNominalCapacity: z.number().min(0),
  withdrawalNominalCapacity: z.number().min(0),
  reservoirCapacity: z.number().min(0),
  efficiency: z.number().min(0),
  initialLevel: z.number().min(0).max(1),
  initialLevelOptim: z.boolean(),
  // Since v8.8; older studies may omit version-specific fields or return null.
  enabled: nullishToOptional(z.boolean()),
  // Since v9.2.
  efficiencyWithdrawal: nullishToOptional(z.number().min(0)),
  penalizeVariationInjection: nullishToOptional(z.boolean()),
  penalizeVariationWithdrawal: nullishToOptional(z.boolean()),
  // Since v9.3.
  allowOverflow: nullishToOptional(z.boolean()),
});

export const storagesSchema = z.array(storageSchema);

export const storageCreationSchema = storageSchema
  .omit({ id: true })
  .partial()
  .required({ name: true });

export const storageUpdateSchema = storageSchema.omit({ id: true, name: true }).partial();
