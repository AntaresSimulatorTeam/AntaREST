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

/**
 * Zod schemas for directories API validation and transformation
 * Schemas are the single source of truth - types are inferred using z.infer<>
 */

////////////////////////////////////////////////////////////////
// Base Schemas
////////////////////////////////////////////////////////////////

const baseDirectorySchema = z.object({
  name: z.string(),
  parentId: z.string().nullable(),
});

////////////////////////////////////////////////////////////////
// Response Schemas
////////////////////////////////////////////////////////////////

export const directorySchema = baseDirectorySchema.extend({
  id: z.string(),
});

export const directoriesListResponseSchema = z.array(directorySchema);

export const updateDirectoryResponseSchema = baseDirectorySchema;

////////////////////////////////////////////////////////////////
// Input Schemas
////////////////////////////////////////////////////////////////

export const createDirectoryInputSchema = z.object({
  name: z.string().min(1),
  parentId: z.string().nullable(), // ID is null for root directory creation
});

export const updateDirectoryInputSchema = z.object({
  name: z.string().min(1),
  parentId: z.string().nullable(), // ID is null for root directory update
});

////////////////////////////////////////////////////////////////
// Filter Schemas
////////////////////////////////////////////////////////////////

export const directoryFiltersSchema = z.object({
  search: z.string().optional(),
  sortBy: z.enum(["name"]).optional(),
  sortOrder: z.enum(["asc", "desc"]).optional(),
});
