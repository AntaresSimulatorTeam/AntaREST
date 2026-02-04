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
import { directoryMutations } from "@/queries/directories/mutations";
import type { Directory } from "@/services/api/directories/types";

interface UseUpdateDirectoryOptions {
  onSuccess?: () => void;
}

export function useUpdateDirectory(options?: UseUpdateDirectoryOptions) {
  const queryClient = useQueryClient();
  const { enqueueSnackbar } = useSnackbar();
  const { t } = useTranslation();

  return useMutation({
    ...directoryMutations.update(),
    onMutate: async ({ id, data: updateData }) => {
      await queryClient.cancelQueries({ queryKey: directoryKeys.all });

      const previousDirectories = queryClient.getQueryData<Directory[]>(directoryKeys.list());

      if (previousDirectories) {
        const updatedDirectories = previousDirectories.map((dir) =>
          dir.id === id
            ? {
                ...dir,
                name: updateData.name,
                parentId: updateData.parentId,
              }
            : dir,
        );

        queryClient.setQueryData<Directory[]>(directoryKeys.list(), updatedDirectories);
      }

      return { previousDirectories };
    },
    onError: (_error, _variables, context) => {
      // Rollback optimistic update
      if (context?.previousDirectories) {
        queryClient.setQueryData(directoryKeys.list(), context.previousDirectories);
      }

      //  TODO use errorSnackbar
      enqueueSnackbar(t("studies.updateFolder.error"), { variant: "error" });
    },
    onSuccess: () => {
      // TODO - check if we need to invalidate the query
      // or we can use the returned data to update the cache
      queryClient.invalidateQueries({ queryKey: directoryKeys.all });
      options?.onSuccess?.();
    },
  });
}
