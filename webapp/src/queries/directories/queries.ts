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

import { queryOptions } from "@tanstack/react-query";
import { directoriesApi } from "@/services/api/directories";
import type { DirectoryFilters } from "@/services/api/directories/types";
import { directoryKeys } from "./keys";

/**
 * Query options for fetching all directories
 * GET /v1/directories
 *
 * @param filters - Optional filters for directories
 * @returns Query options object
 *
 * @example
 * ```tsx
 * const { data, isLoading } = useQuery(directoryQueries.list());
 * ```
 */
export const directoryQueries = {
  /**
   * Base key for all directory queries
   *
   * @returns Array of directory keys
   */
  all: () => directoryKeys.all,

  /**
   * Query options for listing directories
   *
   * @param filters - Optional filters for directories
   * @returns Query options object
   */
  list: (filters?: DirectoryFilters) => {
    return queryOptions({
      queryKey: directoryKeys.list(filters),
      queryFn: () => directoriesApi.getAll(),
      staleTime: 1000 * 60 * 5, // 5 minutes
    });
  },

  /**
   * Query options for a single directory
   * Note: Filters from getAll() since no GET by ID endpoint exists
   *
   * @param directoryId - ID of the directory to fetch
   * @returns Query options object
   */
  detail: (directoryId: string) => {
    return queryOptions({
      queryKey: directoryKeys.detail(directoryId),
      queryFn: async () => {
        const directories = await directoriesApi.getAll();
        const directory = directories.find((d) => d.id === directoryId);

        if (!directory) {
          throw new Error(`Directory with id ${directoryId} not found`);
        }

        return directory;
      },
      enabled: !!directoryId,
    });
  },
};
