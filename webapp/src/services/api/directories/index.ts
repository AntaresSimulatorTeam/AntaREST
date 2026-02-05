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
  directoriesListResponseSchema,
  directorySchema,
  updateDirectoryResponseSchema,
} from "./schemas";
import type {
  CreateDirectoryInput,
  DirectoriesListResponse,
  Directory,
  UpdateDirectoryInput,
  UpdateDirectoryResponse,
} from "./types";

export const directoriesApi = {
  /**
   * GET /v1/directories - List all directories
   *
   * @returns Promise<DirectoriesListResponse> - List of directories data
   * @throws {Error} If the response doesn't match the expected schema
   */
  getAll: async (): Promise<DirectoriesListResponse> => {
    const { data } = await client.get("/v1/directories");
    return directoriesListResponseSchema.parse(data);
  },

  /**
   * POST /v1/directories - Create a new directory
   *
   * @param directoryData - Directory data to create
   * @returns Promise<Directory> - Created directory data
   * @throws {Error} If the response doesn't match the expected schema
   */
  create: async (directoryData: CreateDirectoryInput): Promise<Directory> => {
    const { data } = await client.post("/v1/directories", directoryData);
    return directorySchema.parse(data);
  },

  /**
   * PATCH /v1/directories/{directoryId} - Update directory
   *
   * @param directoryId - ID of the directory to update
   * @param directoryData - Partial directory data to update
   * @returns Promise<Directory> - Updated directory data
   * @throws {Error} If the response doesn't match the expected schema
   */
  update: async (
    directoryId: string,
    directoryData: UpdateDirectoryInput,
  ): Promise<UpdateDirectoryResponse> => {
    const { data } = await client.patch(`/v1/directories/${directoryId}`, directoryData);
    return updateDirectoryResponseSchema.parse(data);
  },

  /**
   * DELETE /v1/directories/{directoryId} - Delete directory
   *
   * @param directoryId - ID of the directory to delete
   * @returns Promise<void>
   */
  delete: async (directoryId: string): Promise<void> => {
    await client.delete(`/v1/directories/${directoryId}`);
  },
};
