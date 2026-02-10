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

// Derived from response schema — single source of truth for field definitions
export const createDirectoryInputSchema = directorySchema.omit({ id: true });

// PATCH allows partial updates — at least one field must be provided
export const updateDirectoryInputSchema = createDirectoryInputSchema
  .partial()
  .refine((data) => Object.keys(data).length > 0, {
    message: "At least one field must be provided for update",
  });
