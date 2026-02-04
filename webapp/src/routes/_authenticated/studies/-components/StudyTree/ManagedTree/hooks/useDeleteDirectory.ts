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
import { useSnackbar } from "notistack";
import { useTranslation } from "react-i18next";
import { directoryKeys } from "@/queries/directories/keys";
import { directoriesApi } from "@/services/api/directories";
import type { Directory } from "@/services/api/directories/types";

interface UseDeleteDirectoryOptions {
  onSuccess?: () => void;
}

interface DeleteDirectoryParams {
  directoryId: string;
  cascade: boolean;
  allDirectories: Directory[];
}

// For cascade deletion - used to move children to parent level
async function moveChildrenToParent(directoryId: string, directories: Directory[]) {
  const directoryToDelete = directories.find((dir) => dir.id === directoryId);
  const children = directories.filter((dir) => dir.parentId === directoryId);
  const newParentId = directoryToDelete?.parentId ?? null;

  await Promise.all(
    children.map((child) =>
      directoriesApi.update(child.id, {
        name: child.name,
        parentId: newParentId,
      }),
    ),
  );
}

// For non-cascade deletion - updates the directory list optimistically
function updateDirectoriesOptimistically(
  directories: Directory[],
  directoryId: string,
): Directory[] {
  const directoryToDelete = directories.find((d) => d.id === directoryId);
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
  const { enqueueSnackbar } = useSnackbar();
  const { t } = useTranslation();

  return useMutation({
    mutationKey: ["deleteDirectory"],
    mutationFn: async ({ directoryId, cascade, allDirectories }: DeleteDirectoryParams) => {
      // If not cascading, move children to parent level first
      if (!cascade) {
        await moveChildrenToParent(directoryId, allDirectories);
      }

      // Delete the directory
      return directoriesApi.delete(directoryId);
    },
    onMutate: async ({ directoryId, cascade }) => {
      await queryClient.cancelQueries({ queryKey: directoryKeys.all });

      const previousDirectories = queryClient.getQueryData<Directory[]>(directoryKeys.list());

      if (previousDirectories) {
        const updatedDirectories = cascade
          ? previousDirectories.filter((dir) => dir.id !== directoryId)
          : updateDirectoriesOptimistically(previousDirectories, directoryId);

        queryClient.setQueryData<Directory[]>(directoryKeys.list(), updatedDirectories);
      }

      return { previousDirectories };
    },
    onError: (_error, _variables, context) => {
      // Rollback optimistic update
      if (context?.previousDirectories) {
        queryClient.setQueryData(directoryKeys.list(), context.previousDirectories);
      }

      // TODO use error snackbar
      enqueueSnackbar(
        t("studies.deleteFolder.error", {
          defaultValue: "Failed to delete directory. Please try again.",
        }),
        { variant: "error" },
      );
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: directoryKeys.all });
      options?.onSuccess?.();
    },
  });
}
