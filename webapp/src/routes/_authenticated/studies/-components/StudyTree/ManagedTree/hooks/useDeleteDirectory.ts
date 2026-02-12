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
import useEnqueueErrorSnackbar from "@/hooks/useEnqueueErrorSnackbar";
import { directoryQueries } from "@/queries/directories/queries";
import { deleteDirectory } from "@/services/api/directories";
import type { Directory } from "@/services/api/directories/types";
import { toError } from "@/utils/fnUtils";

interface UseDeleteDirectoryOptions {
  onSuccess?: () => void;
}

interface DeleteDirectoryParams {
  directoryId: string;
  allDirectories: Directory[];
}

interface DeleteDirectoryContext {
  previousDirectories?: Directory[];
  affectedDirectoryIds: string[];
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

export function useDeleteDirectory(options?: UseDeleteDirectoryOptions) {
  const queryClient = useQueryClient();
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();
  const { t } = useTranslation();

  return useMutation({
    mutationKey: ["deleteDirectory"],
    mutationFn: async ({ directoryId }: DeleteDirectoryParams) => {
      await deleteDirectory(directoryId);
    },
    onMutate: async ({ directoryId, allDirectories }): Promise<DeleteDirectoryContext> => {
      // Cancel only the queries we're about to update
      await queryClient.cancelQueries({ queryKey: directoryQueries.list().queryKey });

      // Snapshot the previous state for rollback
      const previousDirectories = queryClient.getQueryData(directoryQueries.list().queryKey);

      // Track affected directories for cache cleanup (directory + all descendants)
      const affectedDirectoryIds = [
        directoryId,
        ...findAllDescendants(directoryId, allDirectories),
      ];

      // Optimistically remove directory and all descendants from the list
      if (previousDirectories) {
        const updatedDirectories = previousDirectories.filter(
          (dir) => !affectedDirectoryIds.includes(dir.id),
        );

        queryClient.setQueryData(directoryQueries.list().queryKey, updatedDirectories);
      }

      return {
        previousDirectories,
        affectedDirectoryIds,
      };
    },
    onError: (error, _variables, context) => {
      // Rollback optimistic updates
      if (context?.previousDirectories) {
        queryClient.setQueryData(directoryQueries.list().queryKey, context.previousDirectories);
      }

      enqueueErrorSnackbar(t("studies.deleteDirectory.error"), toError(error));
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: directoryQueries.list().queryKey });

      options?.onSuccess?.();
    },
  });
}
