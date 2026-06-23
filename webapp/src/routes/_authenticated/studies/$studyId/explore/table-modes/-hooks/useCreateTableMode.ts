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
import { useParams, useRouter } from "@tanstack/react-router";
import { useTranslation } from "react-i18next";

function useCreateTableMode() {
  const params = useParams({
    from: "/_authenticated/studies/$studyId/explore/table-modes",
  });
  const router = useRouter();
  const queryClient = useQueryClient();
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();
  const { t } = useTranslation();

  const { queryKey: queryListKey } = tableModeQueries.list();

  const isRouterMatchTempTableMode = (tempTableModeId: string) => {
    return router.state.matches.some(
      (m) =>
        m.routeId === "/_authenticated/studies/$studyId/explore/table-modes/$tableModeId/" &&
        m.params.tableModeId === tempTableModeId,
    );
  };

  const mutation = useMutation({
    ...tableModeMutations.create(),
    onMutate: async (variables) => {
      const tempTableModeId = crypto.randomUUID();

      await queryClient.cancelQueries({ queryKey: queryListKey });

      queryClient.setQueryData(queryListKey, (old = []) => {
        return [
          ...old,
          createOptimisticListItem<TableMode>({
            ...variables,
            id: tempTableModeId,
          }),
        ];
      });

      // Await navigation prevents `onError`/`onSuccess` to be called before navigation is done,
      // causing `isRouterMatchTempTableMode()` to not work as expected
      await router.navigate({
        to: "/studies/$studyId/explore/table-modes/$tableModeId",
        params: { ...params, tableModeId: tempTableModeId },
      });

      return tempTableModeId;
    },
    onError: (error, variables, tempTableModeId) => {
      enqueueErrorSnackbar(t("study.tableModes.create.error", { name: variables.name }), error);

      if (!tempTableModeId) {
        return;
      }

      queryClient.setQueryData(queryListKey, (old = []) => {
        return old.filter((tableMode) => tableMode.id !== tempTableModeId);
      });

      if (isRouterMatchTempTableMode(tempTableModeId)) {
        router.navigate({
          to: "/studies/$studyId/explore/table-modes",
          params,
          replace: true,
        });
      }
    },
    onSuccess: (newTableMode, _, tempTableModeId) => {
      queryClient.setQueryData(queryListKey, (old = []) => {
        return old.map((tableMode) =>
          tableMode.id === tempTableModeId ? newTableMode : tableMode,
        );
      });

      if (isRouterMatchTempTableMode(tempTableModeId)) {
        router.navigate({
          to: ".",
          params: { ...params, tableModeId: newTableMode.id },
          replace: true,
        });
      }
    },
  });

  return mutation;
}

export default useCreateTableMode;
