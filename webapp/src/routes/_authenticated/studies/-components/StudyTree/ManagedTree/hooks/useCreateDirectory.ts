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
import { directoryKeys } from "@/queries/directories/keys";
import { directoryMutations } from "@/queries/directories/mutations";
import type { Directory } from "@/services/api/directories/types";
import { toError } from "@/utils/fnUtils";

interface UseCreateDirectoryOptions {
  onSuccess?: (directory: Directory) => void;
}

interface CreateDirectoryContext {
  previousDirectories?: Directory[];
  tempId: string;
}

export function useCreateDirectory(options?: UseCreateDirectoryOptions) {
  const queryClient = useQueryClient();
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();
  const { t } = useTranslation();

  return useMutation({
    ...directoryMutations.create(),
    onMutate: async (newDirectory): Promise<CreateDirectoryContext> => {
      // Generate a temporary ID for optimistic update
      const tempId = `temp-${Date.now()}-${Math.random()}`;

      // Cancel only the list queries we're about to update
      await queryClient.cancelQueries({ queryKey: directoryKeys.lists() });

      // Snapshot the previous state for rollback
      const previousDirectories = queryClient.getQueryData<Directory[]>(directoryKeys.list());

      // Optimistically add the new directory to the list
      if (previousDirectories) {
        const tempDirectory: Directory = {
          id: tempId,
          name: newDirectory.name,
          parentId: newDirectory.parentId,
        };

        queryClient.setQueryData<Directory[]>(directoryKeys.list(), [
          ...previousDirectories,
          tempDirectory,
        ]);
      }

      return { previousDirectories, tempId };
    },
    onError: (error, _newDirectory, context) => {
      // Rollback optimistic update
      if (context?.previousDirectories) {
        queryClient.setQueryData(directoryKeys.list(), context.previousDirectories);
      }

      enqueueErrorSnackbar(t("studies.createFolder.error"), toError(error));
    },
    onSuccess: (data, _variables, context) => {
      // Add the new directory to the detail cache
      queryClient.setQueryData<Directory>(directoryKeys.detail(data.id), data);

      // Update the list cache: replace temp directory with the real one
      queryClient.setQueryData<Directory[]>(directoryKeys.list(), (old) => {
        if (!old) {
          return [data];
        }

        // Replace the temporary directory with the actual one from the server
        return old.map((dir) => (dir.id === context.tempId ? data : dir));
      });

      // No need to invalidate since we're updating the cache directly
      // This prevents unnecessary refetches and UI flicker

      options?.onSuccess?.(data);
    },
  });
}
