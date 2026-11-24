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
import { storageKeys } from "@/queries/storages/keys";
import { storageMutations } from "@/queries/storages/mutations";
import { storageQueries } from "@/queries/storages/queries";
import type { StoragesParams } from "@/services/api/studies/areas/storages/types";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";

function useDeleteStorages({ studyId, areaId }: StoragesParams) {
  const queryClient = useQueryClient();
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();
  const { t } = useTranslation();

  const { queryKey: queryListKey } = storageQueries.list(studyId, areaId);

  return useMutation({
    ...storageMutations.delete(studyId, areaId),
    onMutate: async (variables) => {
      const { storageIds } = variables;

      await queryClient.cancelQueries({ queryKey: queryListKey });

      const prevStorages = queryClient.getQueryData(queryListKey);
      const storagesToDelete = prevStorages?.filter(({ id }) => storageIds.includes(id));

      if (storagesToDelete && storagesToDelete.length > 0) {
        queryClient.setQueryData(queryListKey, (old = []) => {
          return old.filter((storage) => !storageIds.includes(storage.id));
        });
      }

      return { storagesToDelete };
    },
    onError: (error, variables, onMutateResult) => {
      const { storageIds } = variables;
      const { storagesToDelete } = onMutateResult || {};

      enqueueErrorSnackbar(
        t("study.modeling.storages.delete.error", {
          count: storageIds.length,
          names: storagesToDelete?.map((t) => t.name) || storageIds,
        }),
        error,
      );

      if (storagesToDelete) {
        queryClient.setQueryData(queryListKey, (old = []) => [...old, ...storagesToDelete]);
      }
    },
    onSuccess: (_, variables) => {
      const { storageIds } = variables;

      // Remove constraint queries for each deleted storage.
      // Storage IDs are derived from the (normalized) name, so a re-created storage
      // can reuse a deleted one's ID and would inherit its stale cached constraints.
      for (const storageId of storageIds) {
        queryClient.removeQueries({
          queryKey: storageKeys.constraintList(studyId, areaId, storageId),
        });
      }
    },
  });
}

export default useDeleteStorages;
