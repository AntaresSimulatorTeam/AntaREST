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
  workspaces: () => {
    return queryOptions({
      queryKey: explorerKeys.workspaces(),
      queryFn: async () => {
        const data = await api.getWorkspaces();
        return workspacesSchema.parse(data);
      },
    });
  },

  folders: (workspace: string, path: string) => {
    return queryOptions({
      queryKey: explorerKeys.foldersByPath(workspace, path),
      queryFn: async () => {
        const data = await api.getFolders(workspace, path);
        return foldersSchema.parse(data);
      },
      enabled: !!workspace,
    });
  },
};
