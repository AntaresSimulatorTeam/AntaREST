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

/**
 * Query keys factory for explorer (workspaces and folders)
 * Provides centralized query key management for consistent cache handling
 *
 * Key hierarchy:
 * - ['explorer'] - All explorer-related queries
 * - ['explorer', 'workspaces'] - All workspace queries
 * - ['explorer', 'folders'] - All folder queries
 * - ['explorer', 'folders', workspace, path] - Folders for specific workspace and path
 */
export const explorerKeys = {
  all: ["explorer"] as const,
  workspaces: () => [...explorerKeys.all, "workspaces"] as const,
  folders: () => [...explorerKeys.all, "folders"] as const,
  foldersByPath: (workspace: string, path: string) =>
    [...explorerKeys.folders(), workspace, path] as const,
};
