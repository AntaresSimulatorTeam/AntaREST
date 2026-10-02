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
 * Only fetches in desktop mode as workspaces are generated dynamically based on mounted discs.
 * On web mode, this case is almost never used, so we save the API call.
 *
 * @returns Query result with workspaces data
 */
export function useWorkspaces() {
  const { isDesktopMode } = useAppMode();

  return useQuery({
    ...explorerQueries.workspaces(),
    enabled: isDesktopMode,
  });
}
