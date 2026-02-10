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

import client from "../client";
import {
  createDirectoryParamsSchema,
  directoriesResponseSchema,
  directorySchema,
  updateDirectoryParamsSchema,
} from "./schemas";
import type { CreateDirectoryParams, Directory, UpdateDirectoryParams } from "./types";

/**
 * GET /v1/directories - List all directories
 *
 * @returns Promise<Directory[]> - List of directories
 * @throws {ZodError} If the response doesn't match the expected schema
 */
export async function getDirectories(): Promise<Directory[]> {
  const { data } = await client.get("/v1/directories");
  return directoriesResponseSchema.parse(data);
}

/**
 * POST /v1/directories - Create a new directory
 *
 * @param directoryData - Directory data to create
 * @returns Promise<Directory> - Created directory data
 * @throws {ZodError} If the params or response doesn't match the expected schema
 */
export async function createDirectory(directoryData: CreateDirectoryParams): Promise<Directory> {
  const validatedInput = createDirectoryParamsSchema.parse(directoryData);
  const { data } = await client.post("/v1/directories", validatedInput);
  return directorySchema.parse(data);
}

/**
 * PATCH /v1/directories/{directoryId} - Update directory
 *
 * @param params - Update parameters
 * @param params.directoryId - ID of the directory to update
 * @param params.directoryData - Partial directory data to update
 * @returns Promise<Directory> - Updated directory data
 * @throws {ZodError} If the params or response doesn't match the expected schema
 */
export async function updateDirectory({
  directoryId,
  directoryData,
}: {
  directoryId: string;
  directoryData: UpdateDirectoryParams;
}): Promise<Directory> {
  const validatedInput = updateDirectoryParamsSchema.parse(directoryData);
  const { data } = await client.patch(`/v1/directories/${directoryId}`, validatedInput);
  return directorySchema.parse(data);
}

/**
 * DELETE /v1/directories/{directoryId} - Delete directory
 *
 * @param directoryId - ID of the directory to delete
 * @returns Promise<void>
 */
export async function deleteDirectory(directoryId: string): Promise<void> {
  await client.delete(`/v1/directories/${directoryId}`);
}
