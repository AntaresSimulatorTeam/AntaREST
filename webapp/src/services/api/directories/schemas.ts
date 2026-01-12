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
 * Following Zod best practices:
 * - Schemas are the single source of truth
 * - Use .transform() to convert API responses to frontend DTOs
 * - Types are inferred from schemas using z.infer<>
 */

////////////////////////////////////////////////////////////////
// API Response Schemas
////////////////////////////////////////////////////////////////


const apiDirectorySchema = z.object({
  id: z.string(),
  name: z.string(),
  description: z.string().optional(),
  path: z.string().optional(),
  created_at: z.string(),
  updated_at: z.string(),
});


const apiDirectoriesListResponseSchema = z.object({
  directories: z.array(apiDirectorySchema),
  total: z.number().optional(),
});

////////////////////////////////////////////////////////////////
// Transformed Schemas (adapters)
////////////////////////////////////////////////////////////////


export const directorySchema = apiDirectorySchema.transform((data) => ({
  id: data.id,
  name: data.name,
  description: data.description,
  path: data.path,
  createdAt: data.created_at,
  updatedAt: data.updated_at,
}));


export const directoriesListResponseSchema =
  apiDirectoriesListResponseSchema.transform((data) => ({
    directories: data.directories.map((directory) => ({
      id: directory.id,
      name: directory.name,
      description: directory.description,
      path: directory.path,
      createdAt: directory.created_at,
      updatedAt: directory.updated_at,
    })),
    total: data.total,
  }));

////////////////////////////////////////////////////////////////
// Input Schemas (mutations)
////////////////////////////////////////////////////////////////


export const createDirectoryInputSchema = z.object({
  name: z.string().min(1, "Name is required"),
  description: z.string().optional(),
  path: z.string().optional(),
});


export const updateDirectoryInputSchema = z.object({
  name: z.string().min(1).optional(),
  description: z.string().optional(),
  path: z.string().optional(),
});


export const directoryFiltersSchema = z.object({
  search: z.string().optional(),
  sortBy: z.enum(["name", "created_at", "updated_at"]).optional(),
  sortOrder: z.enum(["asc", "desc"]).optional(),
});
