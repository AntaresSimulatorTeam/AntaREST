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

import { useQueryClient } from "@tanstack/react-query";
import { useCallback, useState } from "react";
import { useTranslation } from "react-i18next";
import { DEFAULT_WORKSPACE_NAME } from "@/components/utils/constants";
import useEnqueueErrorSnackbar from "@/hooks/useEnqueueErrorSnackbar";
import { explorerQueries } from "@/queries/explorer/queries";
import type { FolderDTO } from "@/queries/explorer/schemas";
import { toError } from "@/utils/fnUtils";

/**
 * Hook to manage folder exploration in the study tree.
 * Handles fetching subfolders when a user expands a folder node.
 *
 * @returns Object with methods and state for folder exploration
 */
export function useFolderExplorer() {
  const queryClient = useQueryClient();
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();
  const [t] = useTranslation();
  const [exploredFolders, setExploredFolders] = useState<string[]>([]);
  const [itemsLoading, setItemsLoading] = useState<string[]>([]);

  /**
   * Parses a path and extracts workspace and subpath components.
   * Validates that the path is absolute and has a valid workspace.
   *
   * @param itemId - The path to parse (e.g., "/workspace/sub/path")
   * @returns Parsed path components or null if invalid
   */
  const parsePath = useCallback((itemId: string) => {
    const [root, workspace, ...subPath] = itemId.split("/");

    const isAbsolutePath = root === ""; // Path must start with a '/'
    const isValidWorkspace = workspace && workspace !== DEFAULT_WORKSPACE_NAME;

    if (!isAbsolutePath || !isValidWorkspace) {
      return null;
    }

    return { workspace, path: subPath.join("/") };
  }, []);

  /**
   * Fetches and caches folders for a given path.
   * This is called when the user clicks on a folder to explore its contents.
   *
   * The study tree is built from scanned studies in the database, but this scan process
   * can take a long time. Instead of waiting for the scan, users can walk into the tree
   * and trigger a scan only when needed by expanding folders.
   *
   * @param itemId - The full path of the folder to explore (e.g., "/workspace/sub/path")
   * @returns Promise that resolves when folders are fetched, or null if path is invalid
   */
  const explorePath = useCallback(
    async (itemId: string): Promise<FolderDTO[] | null> => {
      const parsed = parsePath(itemId);

      if (!parsed) {
        return null;
      }

      const { workspace, path } = parsed;

      setItemsLoading((prev) => [...prev, itemId]);

      try {
        const folders = await queryClient.fetchQuery(explorerQueries.folders(workspace, path));

        // Mark this path as explored
        setExploredFolders((prev) => {
          if (prev.includes(itemId)) {
            return prev;
          }
          return [...prev, itemId];
        });

        return folders;
      } catch (err) {
        enqueueErrorSnackbar(
          t("studies.tree.error.failToFetchFolder", {
            path: itemId,
            interpolation: { escapeValue: false },
          }),
          toError(err),
        );
        return null;
      } finally {
        setItemsLoading((prev) => prev.filter((id) => id !== itemId));
      }
    },
    [parsePath, queryClient, enqueueErrorSnackbar, t],
  );

  return {
    explorePath,
    exploredFolders,
    itemsLoading,
  };
}
