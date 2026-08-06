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
import { getNextItemAfterDeletion } from "@/utils/arrayUtils";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useParams, useRouter } from "@tanstack/react-router";
import { useTranslation } from "react-i18next";
import { tableModesToList } from "../-utils";

function useDeleteTableMode() {
  const params = useParams({
    from: "/_authenticated/studies/$studyId/explore/table-modes",
  });
  const router = useRouter();
  const queryClient = useQueryClient();
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();
  const { t } = useTranslation();

  const { queryKey: queryListKey } = tableModeQueries.list();

  const mutation = useMutation({
    ...tableModeMutations.delete(),
    onMutate: async (variables) => {
      const { tableId: tableModeToDeleteId } = variables;

      await queryClient.cancelQueries({ queryKey: queryListKey });

      const prevTableModes = queryClient.getQueryData(queryListKey);
      const tableModeToDelete = prevTableModes?.find(
        (tableMode) => tableMode.id === tableModeToDeleteId,
      );

      if (tableModeToDelete) {
        queryClient.setQueryData(queryListKey, (old) => {
          return old?.filter((tableMode) => tableMode.id !== tableModeToDeleteId);
        });
      }

      const prevList = prevTableModes && tableModesToList(prevTableModes);

      const nextTableMode = prevList
        ? getNextItemAfterDeletion(
            prevList,
            prevList.findIndex((item) => item.id === tableModeToDeleteId),
          )
        : undefined;

      router.navigate({
        to: nextTableMode
          ? "/studies/$studyId/explore/table-modes/$tableModeId"
          : "/studies/$studyId/explore/table-modes",
        params: {
          ...params,
          tableModeId: nextTableMode?.id,
        },
        replace: true,
      });

      return { tableModeToDelete };
    },
    onError: (error, variables, onMutateResult) => {
      const { tableModeToDelete } = onMutateResult || {};

      enqueueErrorSnackbar(
        t("study.tableModes.delete.error", {
          name: tableModeToDelete?.name || variables.tableId,
        }),
        error,
      );

      if (tableModeToDelete) {
        queryClient.setQueryData(queryListKey, (old = []) => [...old, tableModeToDelete]);
      }
    },
  });

  return mutation;
}

export default useDeleteTableMode;
