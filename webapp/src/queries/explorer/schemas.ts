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

export const workspaceSchema = z.object({
  name: z.string(),
  diskName: z.string(),
});

export const folderSchema = z.object({
  name: z.string(),
  path: z.string(),
  workspace: z.string(),
  parentPath: z.string(),
  hasChildren: z.boolean().optional(),
  isStudyFolder: z.boolean().optional(),
});

export const workspacesSchema = z.array(workspaceSchema);
export const foldersSchema = z.array(folderSchema);

export type WorkspaceDTO = z.infer<typeof workspaceSchema>;
export type FolderDTO = z.infer<typeof folderSchema>;
