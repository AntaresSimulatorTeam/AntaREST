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

interface UseUpdateDirectoryOptions {
  onSuccess?: () => void;
}

interface UpdateDirectoryContext {
  previousDirectories?: Directory[];
  previousDetail?: Directory;
}

export function useUpdateDirectory(options?: UseUpdateDirectoryOptions) {
  const queryClient = useQueryClient();
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();
  const { t } = useTranslation();

  return useMutation({
    ...directoryMutations.update(),
    onMutate: async ({ id, data: updateData }): Promise<UpdateDirectoryContext> => {
      // Cancel only the queries we're about to update
      await queryClient.cancelQueries({ queryKey: directoryKeys.lists() });
      await queryClient.cancelQueries({ queryKey: directoryKeys.detail(id) });

      // Snapshot the previous state for rollback
      const previousDirectories = queryClient.getQueryData<Directory[]>(directoryKeys.list());
      const previousDetail = queryClient.getQueryData<Directory>(directoryKeys.detail(id));

      // Optimistically update the directory list
      queryClient.setQueryData<Directory[]>(directoryKeys.list(), (old) =>
        old?.map((dir) => (dir.id === id ? { ...dir, ...updateData } : dir)),
      );

      // Optimistically update the directory detail if cached
      if (previousDetail) {
        queryClient.setQueryData<Directory>(directoryKeys.detail(id), {
          ...previousDetail,
          ...updateData,
        });
      }

      return { previousDirectories, previousDetail };
    },
    onError: (error, { id }, context) => {
      // Rollback optimistic updates
      if (context?.previousDirectories) {
        queryClient.setQueryData(directoryKeys.list(), context.previousDirectories);
      }
      if (context?.previousDetail) {
        queryClient.setQueryData(directoryKeys.detail(id), context.previousDetail);
      }

      enqueueErrorSnackbar(t("studies.updateDirectory.error"), toError(error));
    },
    onSuccess: (data, { id }) => {
      // Update cache with server response to ensure consistency
      queryClient.setQueryData<Directory>(directoryKeys.detail(id), data);

      // Update the directory in the list with server response
      queryClient.setQueryData<Directory[]>(directoryKeys.list(), (old) =>
        old?.map((dir) => (dir.id === id ? data : dir)),
      );

      // No need to invalidate since we're updating the cache directly
      // This prevents unnecessary refetches and UI flicker

      options?.onSuccess?.();
    },
  });
}
