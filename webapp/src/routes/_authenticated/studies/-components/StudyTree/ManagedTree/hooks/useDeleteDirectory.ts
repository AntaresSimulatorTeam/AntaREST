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

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";
import { directoryKeys } from "@/queries/directories/keys";
import { updateDirectory, deleteDirectory } from "@/services/api/directories";
import type { Directory } from "@/services/api/directories/types";
import useEnqueueErrorSnackbar from "@/hooks/useEnqueueErrorSnackbar";
import { toError } from "@/utils/fnUtils";

interface UseDeleteDirectoryOptions {
  onSuccess?: () => void;
}

interface DeleteDirectoryParams {
  directoryId: string;
  cascade: boolean;
  allDirectories: Directory[];
}

interface DeleteDirectoryContext {
  previousDirectories?: Directory[];
  affectedDirectoryIds: string[];
  movedChildren?: Directory[];
}

/**
 * Recursively finds all descendant directory IDs
 *
 * @param directoryId - The ID of the directory to find descendants for
 * @param directories - The list of directories to search
 * @returns An array of descendant directory IDs
 */
function findAllDescendants(directoryId: string, directories: Directory[]): string[] {
  const children = directories.filter((dir) => dir.parentId === directoryId);
  const childIds = children.map((child) => child.id);
  const descendantIds = children.flatMap((child) => findAllDescendants(child.id, directories));

  return [...childIds, ...descendantIds];
}

/**
 * Moves children to parent level before deletion (non-cascade mode)
 *
 * @param directoryId - The ID of the directory to move children from
 * @param directories - The list of directories to search
 * @returns The updated list of directories
 */
async function moveChildrenToParent(
  directoryId: string,
  directories: Directory[],
): Promise<Directory[]> {
  const directoryToDelete = directories.find((dir) => dir.id === directoryId);
  const children = directories.filter((dir) => dir.parentId === directoryId);
  const newParentId = directoryToDelete?.parentId ?? null;

  await Promise.all(
    children.map((child) =>
      updateDirectory(child.id, {
        name: child.name,
        parentId: newParentId,
      }),
    ),
  );

  return children;
}

/**
 * Updates the directory list optimistically for non-cascade deletion
 *
 * @param directories - The current list of directories
 * @param directoryId - The ID of the directory to delete
 * @returns The updated list of directories
 */
function updateDirectoriesOptimistically(
  directories: Directory[],
  directoryId: string,
): Directory[] {
  const directoryToDelete = directories.find((dir) => dir.id === directoryId);
  const newParentId = directoryToDelete?.parentId ?? null;

  return directories
    .map((dir) => {
      // Move children to parent level
      if (dir.parentId === directoryId) {
        return { ...dir, parentId: newParentId };
      }

      return dir;
    })
    .filter((dir) => dir.id !== directoryId);
}

export function useDeleteDirectory(options?: UseDeleteDirectoryOptions) {
  const queryClient = useQueryClient();
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();
  const { t } = useTranslation();

  return useMutation({
    mutationKey: ["deleteDirectory"],
    mutationFn: async ({ directoryId, cascade, allDirectories }: DeleteDirectoryParams) => {
      // If not cascading, move children to parent level first
      if (!cascade) {
        await moveChildrenToParent(directoryId, allDirectories);
      }

      // Delete the directory
      return deleteDirectory(directoryId);
    },
    onMutate: async ({ directoryId, cascade, allDirectories }): Promise<DeleteDirectoryContext> => {
      // Cancel only the queries we're about to update
      await queryClient.cancelQueries({ queryKey: directoryKeys.lists() });
      await queryClient.cancelQueries({ queryKey: directoryKeys.details() });

      // Snapshot the previous state for rollback
      const previousDirectories = queryClient.getQueryData<Directory[]>(directoryKeys.list());

      // Track affected directories for cache cleanup
      const affectedDirectoryIds = cascade
        ? [directoryId, ...findAllDescendants(directoryId, allDirectories)]
        : [directoryId];

      // Optimistically update the directory list
      if (previousDirectories) {
        const updatedDirectories = cascade
          ? // Cascade: Remove directory and all descendants
            previousDirectories.filter((dir) => !affectedDirectoryIds.includes(dir.id))
          : // Non-cascade: Move children to parent level and remove directory
            updateDirectoriesOptimistically(previousDirectories, directoryId);

        queryClient.setQueryData<Directory[]>(directoryKeys.list(), updatedDirectories);

        // Update detail cache for moved children (non-cascade only)
        if (!cascade) {
          const directoryToDelete = previousDirectories.find((dir) => dir.id === directoryId);
          const newParentId = directoryToDelete?.parentId ?? null;
          const children = previousDirectories.filter((dir) => dir.parentId === directoryId);

          children.forEach((child) => {
            queryClient.setQueryData<Directory>(directoryKeys.detail(child.id), {
              ...child,
              parentId: newParentId,
            });
          });
        }
      }

      return {
        previousDirectories,
        affectedDirectoryIds,
        movedChildren: cascade
          ? undefined
          : allDirectories.filter((dir) => dir.parentId === directoryId),
      };
    },
    onError: (error, _variables, context) => {
      // Rollback optimistic updates
      if (context?.previousDirectories) {
        queryClient.setQueryData(directoryKeys.list(), context.previousDirectories);
      }

      // Rollback detail cache for moved children
      if (context?.movedChildren) {
        context.movedChildren.forEach((child) => {
          queryClient.setQueryData<Directory>(directoryKeys.detail(child.id), child);
        });
      }

      enqueueErrorSnackbar(t("studies.deleteDirectory.error"), toError(error));
    },
    onSuccess: (_data, _variables, context) => {
      // Remove deleted directories from detail cache
      context.affectedDirectoryIds.forEach((id) => {
        queryClient.removeQueries({ queryKey: directoryKeys.detail(id) });
      });

      // Cache is already updated optimistically and doesn't need invalidation
      // This prevents unnecessary refetches and UI flicker

      options?.onSuccess?.();
    },
  });
}
