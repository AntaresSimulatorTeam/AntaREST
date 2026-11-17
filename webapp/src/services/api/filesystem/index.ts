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

import client from "@/services/api/client";
import { workspaceDiskUsageSchema } from "./schemas";
import type { WorkspaceDiskUsage } from "./types";

/**
 * GET /v1/filesystem/ws/{workspace} - Gets the capacity of the filesystem hosting a workspace.
 *
 * @param workspace - Workspace mount name, including "default" for managed studies.
 * @returns Filesystem byte counts shared by all users.
 * @throws If the request fails, the filesystem is unavailable or the response has invalid byte counts.
 */
export async function getWorkspaceDiskUsage(workspace: string): Promise<WorkspaceDiskUsage> {
  const response = await client.get(`/v1/filesystem/ws/${encodeURIComponent(workspace)}`);

  return workspaceDiskUsageSchema.parse(response.data);
}
