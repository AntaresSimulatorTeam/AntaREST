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

import { useQuery } from "@tanstack/react-query";
import { useAppMode } from "@/hooks/useAppMode";
import { explorerQueries } from "@/queries/explorer/queries";

/**
 * Hook to fetch workspaces.
 * Fetches in desktop mode, or on demand when revealing a folder in a web workspace
 * that cannot be derived from the available studies.
 *
 * @param options - Whether the caller needs workspaces outside desktop mode.
 * @param options.enabled - Enable the query on demand in web mode.
 * @returns Query result with workspaces data
 */
export function useWorkspaces({ enabled = false }: { enabled?: boolean } = {}) {
  const { isDesktopMode } = useAppMode();

  return useQuery({
    ...explorerQueries.workspaces(),
    enabled: isDesktopMode || enabled,
  });
}
