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
import { RENEWABLE_GROUPS, TS_INTERPRETATION_OPTIONS } from "./constants";

export const renewableGroupSchema = z.enum(RENEWABLE_GROUPS);

export const renewableClusterSchema = z.object({
  id: z.string(),
  name: z.string(),
  // Before v9.3, non-null groups are mapped to the values in renewableGroupSchema.
  // Since v9.3, groups can be custom strings. The API also permits null.
  group: z.string().nullable(),
  tsInterpretation: z.enum(TS_INTERPRETATION_OPTIONS),
  enabled: z.boolean(),
  unitCount: z.number().int().min(1),
  nominalCapacity: z.number().min(0),
});

export const renewableClustersSchema = z.array(renewableClusterSchema);

// Null write values are ignored by the backend, including group; they do not clear fields.
export const renewableClusterUpdateSchema = z.object({
  group: nullishToOptional(renewableClusterSchema.shape.group.unwrap()),
  tsInterpretation: nullishToOptional(renewableClusterSchema.shape.tsInterpretation),
  enabled: nullishToOptional(renewableClusterSchema.shape.enabled),
  unitCount: nullishToOptional(renewableClusterSchema.shape.unitCount),
  nominalCapacity: nullishToOptional(renewableClusterSchema.shape.nominalCapacity),
});

export const renewableClusterCreationSchema = renewableClusterUpdateSchema.extend({
  name: renewableClusterSchema.shape.name,
});
