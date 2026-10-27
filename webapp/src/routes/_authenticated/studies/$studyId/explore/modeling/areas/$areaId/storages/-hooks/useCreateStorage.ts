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
import { storageMutations } from "@/queries/storages/mutations";
import { storageQueries } from "@/queries/storages/queries";
import { createOptimisticListItem } from "@/queries/utils";
import type { Storage, StoragesParams } from "@/services/api/studies/areas/storages/types";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import * as R from "ramda";
import * as RA from "ramda-adjunct";
import { useTranslation } from "react-i18next";
import { DEFAULT_STORAGE_VALUES } from "../-constants";

function useCreateStorage({ studyId, areaId }: StoragesParams) {
  const queryClient = useQueryClient();
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();
  const { t } = useTranslation();

  const { queryKey: queryListKey } = storageQueries.list(studyId, areaId);

  const mutation = useMutation({
    ...storageMutations.create(studyId, areaId),
    onMutate: async ({ values }) => {
      const tempStorageId = crypto.randomUUID();

      await queryClient.cancelQueries({ queryKey: queryListKey });

      queryClient.setQueryData(queryListKey, (old = []) => {
        return [
          ...old,
          createOptimisticListItem<Storage>({
            ...DEFAULT_STORAGE_VALUES,
            ...R.reject(RA.isUndefined, values),
            id: tempStorageId,
          }),
        ];
      });

      return tempStorageId;
    },
    onError: (error, variables, tempStorageId) => {
      enqueueErrorSnackbar(
        t("study.modeling.storages.create.error", { name: variables.values.name }),
        error,
      );

      if (!tempStorageId) {
        return;
      }

      queryClient.setQueryData(queryListKey, (old = []) => {
        return old.filter((storage) => storage.id !== tempStorageId);
      });
    },
    onSuccess: async (newStorage, _, tempStorageId) => {
      await queryClient.cancelQueries({ queryKey: queryListKey });

      queryClient.setQueryData(queryListKey, (old = []) => {
        return old.map((storage) => (storage.id === tempStorageId ? newStorage : storage));
      });
    },
  });

  return mutation;
}

export default useCreateStorage;
