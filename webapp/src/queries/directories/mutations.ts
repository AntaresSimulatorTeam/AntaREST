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

import { mutationOptions } from "@tanstack/react-query";
import { directoriesApi } from "@/services/api/directories";
import type { CreateDirectoryInput, UpdateDirectoryInput } from "@/services/api/directories/types";

/**
 * Mutation options for directory-related mutations
 * These are used with TanStack Query's useMutation hook
 */

export const directoryMutations = {
  /**
   * Mutation options for creating a new directory
   * POST /v1/directories
   *
   * @returns A promise that resolves when the directory is created.
   * @example
   * ```tsx
   * const { mutate } = useMutation({
   *   ...directoryMutations.create(),
   *   onSuccess: (data) => {
   *     queryClient.invalidateQueries({ queryKey: directoryKeys.lists() });
   *   }
   * });
   *
   * mutate({ name: 'New Folder', path: '/studies/my-study' });
   * ```
   */
  create: () => {
    return mutationOptions({
      mutationKey: ["createDirectory"],
      mutationFn: (directoryData: CreateDirectoryInput) => directoriesApi.create(directoryData),
    });
  },

  /**
   * Mutation options for updating a directory
   * PATCH /v1/directories/{directory_id}
   *
   * @returns A promise that resolves when the directory is updated.
   * @example
   * ```tsx
   * const { mutate } = useMutation({
   *   ...directoryMutations.update(),
   *   onSuccess: (data, { id }) => {
   *     queryClient.setQueryData(directoryKeys.detail(id), data);
   *     queryClient.invalidateQueries({ queryKey: directoryKeys.lists() });
   *   }
   * });
   *
   * mutate({ id: 'dir-123', data: { name: 'Renamed Folder' } });
   * ```
   */
  update: () => {
    return mutationOptions({
      mutationKey: ["updateDirectory"],
      mutationFn: ({ id, data }: { id: string; data: UpdateDirectoryInput }) =>
        directoriesApi.update(id, data),
    });
  },

  /**
   * Mutation options for deleting a directory
   * DELETE /v1/directories/{directory_id}
   *
   * @returns A promise that resolves when the directory is deleted.
   * @example
   * ```tsx
   * const { mutate } = useMutation({
   *   ...directoryMutations.delete(),
   *   onSuccess: (_, directoryId) => {
   *     queryClient.removeQueries({ queryKey: directoryKeys.detail(directoryId) });
   *     queryClient.invalidateQueries({ queryKey: directoryKeys.lists() });
   *   }
   * });
   *
   * mutate('dir-123');
   * ```
   */
  delete: () => {
    return mutationOptions({
      mutationKey: ["deleteDirectory"],
      mutationFn: (directoryId: string) => directoriesApi.delete(directoryId),
    });
  },
};
