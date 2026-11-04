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
import { z } from "zod";
import { RENEWABLE_GROUPS, TS_INTERPRETATION_OPTIONS } from "./constants";

export const renewableGroupSchema = z.enum(RENEWABLE_GROUPS);

export const renewableClusterSchema = z.object({
  // Backend models preserve name casing, while database storage lowercases IDs.
  // TODO: Remove normalization once the backend returns consistent IDs.
  id: z.string().transform(nameToId),
  name: z.string(),
  // Before v9.3, `group` was restricted to the predefined groups (see `renewableGroupSchema`).
  // Since v9.3, it can be any custom string.
  group: z.string(),
  tsInterpretation: z.enum(TS_INTERPRETATION_OPTIONS),
  enabled: z.boolean(),
  unitCount: z.number().int().min(1),
  nominalCapacity: z.number().min(0),
});

export const renewableClustersSchema = z.array(renewableClusterSchema);

export const renewableClusterCreationSchema = renewableClusterSchema
  .omit({ id: true })
  .partial()
  .required({ name: true });

export const renewableClusterUpdateSchema = renewableClusterSchema
  .omit({ id: true, name: true })
  .partial();
