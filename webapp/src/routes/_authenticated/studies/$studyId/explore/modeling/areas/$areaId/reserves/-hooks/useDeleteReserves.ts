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
import { reserveMutations } from "@/queries/reserves/mutations";
import { reserveQueries } from "@/queries/reserves/queries";
import type { ReservesParams } from "@/services/api/studies/areas/reserves/types";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";

function useDeleteReserves({ studyId, areaId }: ReservesParams) {
  const queryClient = useQueryClient();
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();
  const { t } = useTranslation();

  const { queryKey: queryListKey } = reserveQueries.list(studyId, areaId);

  return useMutation({
    ...reserveMutations.delete(studyId, areaId),
    onMutate: async (variables) => {
      const { reserveIds } = variables;

      await queryClient.cancelQueries({ queryKey: queryListKey });

      const prevReserves = queryClient.getQueryData(queryListKey);
      const reservesToDelete = prevReserves?.filter(({ id }) => reserveIds.includes(id));

      if (reservesToDelete && reservesToDelete.length > 0) {
        queryClient.setQueryData(queryListKey, (old = []) => {
          return old.filter((reserve) => !reserveIds.includes(reserve.id));
        });
      }

      return { reservesToDelete };
    },
    onError: (error, variables, onMutateResult) => {
      const { reserveIds } = variables;
      const { reservesToDelete } = onMutateResult || {};

      enqueueErrorSnackbar(
        t("study.modeling.reserves.delete.error", {
          count: reserveIds.length,
          names: reservesToDelete?.map((t) => t.name) || reserveIds,
        }),
        error,
      );

      if (reservesToDelete) {
        queryClient.setQueryData(queryListKey, (old = []) => [...old, ...reservesToDelete]);
      }
    },
  });
}

export default useDeleteReserves;
