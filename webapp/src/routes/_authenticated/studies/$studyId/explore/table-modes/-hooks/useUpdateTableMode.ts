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
import { tableModeMutations } from "@/queries/tableMode/mutations";
import { tableModeQueries } from "@/queries/tableMode/queries";
import { createOptimisticListItem } from "@/queries/utils";
import type { TableMode } from "@/services/api/tablemode/types";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";

function useUpdateTableMode() {
  const queryClient = useQueryClient();
  const { t } = useTranslation();
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();

  const { queryKey: queryListKey } = tableModeQueries.list();

  const mutation = useMutation({
    ...tableModeMutations.update(),
    onMutate: async ({ tableId, ...update }) => {
      await queryClient.cancelQueries({ queryKey: queryListKey });

      const prevTableMode = queryClient
        .getQueryData(queryListKey)
        ?.find((tableMode) => tableMode.id === tableId);

      if (prevTableMode) {
        queryClient.setQueryData(queryListKey, (old = []) => {
          return old.map((tableMode) =>
            tableMode.id === tableId
              ? createOptimisticListItem<TableMode>({
                  ...tableMode,
                  ...update,
                })
              : tableMode,
          );
        });
      }

      return { prevTableMode };
    },
    onError: (error, variables, onMutateResult) => {
      const { prevTableMode } = onMutateResult || {};

      enqueueErrorSnackbar(
        t("study.tableModes.update.error", { name: prevTableMode?.name || variables.tableId }),
        error,
      );

      if (prevTableMode) {
        queryClient.setQueryData(queryListKey, (old = []) => {
          return old.map((tableMode) =>
            tableMode.id === prevTableMode.id ? prevTableMode : tableMode,
          );
        });
      }
    },
    onSuccess: (updatedTableMode) => {
      queryClient.setQueryData(queryListKey, (old = []) => {
        return old.map((tableMode) =>
          tableMode.id === updatedTableMode.id ? updatedTableMode : tableMode,
        );
      });
    },
  });

  return mutation;
}

export default useUpdateTableMode;
