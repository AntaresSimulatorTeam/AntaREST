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

import useEnqueueErrorSnackbar from "@/hooks/useEnqueueErrorSnackbar";
import { directoryMutations } from "@/queries/directories/mutations";
import { directoryQueries } from "@/queries/directories/queries";
import type { Directory } from "@/services/api/directories/types";
import { toError } from "@/utils/fnUtils";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";

interface UseUpdateDirectoryOptions {
  onSuccess?: () => void;
}

interface UpdateDirectoryContext {
  previousDirectories?: Directory[];
}

export function useUpdateDirectory(options?: UseUpdateDirectoryOptions) {
  const queryClient = useQueryClient();
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();
  const { t } = useTranslation();

  return useMutation({
    ...directoryMutations.update(),
    onMutate: async ({ id, data: updateData }): Promise<UpdateDirectoryContext> => {
      // Cancel only the queries we're about to update
      await queryClient.cancelQueries({ queryKey: directoryQueries.list().queryKey });

      // Snapshot the previous state for rollback
      const previousDirectories = queryClient.getQueryData(directoryQueries.list().queryKey);

      // Optimistically update the directory list
      queryClient.setQueryData(directoryQueries.list().queryKey, (old) =>
        old?.map((dir) => (dir.id === id ? { ...dir, ...updateData } : dir)),
      );

      return { previousDirectories };
    },
    onError: (error, _variables, context) => {
      // Rollback optimistic updates
      if (context?.previousDirectories) {
        queryClient.setQueryData(directoryQueries.list().queryKey, context.previousDirectories);
      }

      enqueueErrorSnackbar(t("studies.updateDirectory.error"), toError(error));
    },
    onSuccess: (data, { id }) => {
      // Update the directory in the list with server response
      queryClient.setQueryData(directoryQueries.list().queryKey, (old) =>
        old?.map((dir) => (dir.id === id ? data : dir)),
      );

      // Update the directory name in favorites if it exists there
      queryClient.setQueryData(directoryQueries.favorites().queryKey, (old) =>
        old?.map((fav) => (fav.directoryId === id ? { ...fav, directoryName: data.name } : fav)),
      );

      // No need to invalidate since we're updating the cache directly
      // This prevents unnecessary refetches and UI flicker

      options?.onSuccess?.();
    },
  });
}
