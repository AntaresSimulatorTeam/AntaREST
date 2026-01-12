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

import type { DirectoryFilters } from "@/services/api/directories/types";

/**
 * Query keys factory for directories
 * Provides centralized query key management for consistent cache handling
 *
 * Key hierarchy:
 * - ['directories'] - All directory-related queries
 * - ['directories', 'list'] - All list queries
 * - ['directories', 'list', filters] - List with specific filters
 * - ['directories', 'detail'] - All detail queries
 * - ['directories', 'detail', id] - Specific directory detail
 */
export const directoryKeys = {
  all: ["directories"] as const,
  lists: () => [...directoryKeys.all, "list"] as const,
  list: (filters?: DirectoryFilters) => [...directoryKeys.lists(), filters] as const,
  details: () => [...directoryKeys.all, "detail"] as const,
  detail: (id: string) => [...directoryKeys.details(), id] as const,
};
