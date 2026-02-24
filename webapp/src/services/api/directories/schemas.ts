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

import { z } from "zod";

////////////////////////////////////////////////////////////////
// Response Schemas
////////////////////////////////////////////////////////////////

export const directorySchema = z.object({
  id: z.string(),
  name: z.string().min(1),
  parentId: z.string().nullable(), // null for root directories
});

export const directoriesResponseSchema = z.array(directorySchema);

////////////////////////////////////////////////////////////////
// Input Schemas
////////////////////////////////////////////////////////////////

export const createDirectoryParamsSchema = directorySchema.omit({ id: true });

export const updateDirectoryParamsSchema = z.object({
  id: directorySchema.shape.id,
  data: directorySchema.omit({ id: true }).partial(),
});
