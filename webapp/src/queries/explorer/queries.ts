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
import * as api from "@/services/api/study";
import { explorerKeys } from "./keys";
import { foldersSchema, workspacesSchema } from "./schemas";

export const explorerQueries = {
  /**
   * Query options for fetching workspaces
   * GET /v1/private/explorer/_list_workspaces
   *
   * @returns Query options object
   *
   * @example
   * ```tsx
   * const { data: workspaces } = useQuery(explorerQueries.workspaces());
   * ```
   */
  workspaces: () => {
    return queryOptions({
      queryKey: explorerKeys.workspaces(),
      queryFn: async () => {
        const data = await api.getWorkspaces();
        return workspacesSchema.parse(data);
      },
      staleTime: 1000 * 60 * 5, // 5 minutes
    });
  },

  /**
   * Query options for fetching folders in a workspace path
   *
   * @param workspace - Workspace name
   * @param path - Path relative to workspace root
   * @returns Query options object
   *
   * @example
   * ```tsx
   * const { data: folders } = useQuery(explorerQueries.folders("default", "path/to/folder"));
   * ```
   */
  folders: (workspace: string, path: string) => {
    return queryOptions({
      queryKey: explorerKeys.foldersByPath(workspace, path),
      queryFn: async () => {
        const data = await api.getFolders(workspace, path);
        return foldersSchema.parse(data);
      },
      staleTime: 1000 * 60, // 1 minute
      enabled: !!workspace,
    });
  },
};
