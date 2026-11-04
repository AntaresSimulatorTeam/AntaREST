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
import { createOptimisticListItem } from "@/queries/utils";
import type { Reserve, ReservesParams } from "@/services/api/studies/areas/reserves/types";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import * as R from "ramda";
import * as RA from "ramda-adjunct";
import { useTranslation } from "react-i18next";
import { DEFAULT_RESERVE_VALUES } from "../-constants";

function useCreateReserve({ studyId, areaId }: ReservesParams) {
  const queryClient = useQueryClient();
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();
  const { t } = useTranslation();

  const { queryKey: queryListKey } = reserveQueries.list(studyId, areaId);

  const mutation = useMutation({
    ...reserveMutations.create(studyId, areaId),
    onMutate: async ({ data }) => {
      const tempReserveId = crypto.randomUUID();

      await queryClient.cancelQueries({ queryKey: queryListKey });

      queryClient.setQueryData(queryListKey, (old = []) => {
        return [
          ...old,
          createOptimisticListItem<Reserve>({
            ...DEFAULT_RESERVE_VALUES,
            ...R.reject(RA.isUndefined, data),
            id: tempReserveId,
          }),
        ];
      });

      return tempReserveId;
    },
    onError: (error, variables, tempReserveId) => {
      enqueueErrorSnackbar(
        t("study.modeling.reserves.create.error", { name: variables.data.name }),
        error,
      );

      if (!tempReserveId) {
        return;
      }

      queryClient.setQueryData(queryListKey, (old = []) => {
        return old.filter((reserve) => reserve.id !== tempReserveId);
      });
    },
    onSuccess: async (newReserve, _, tempReserveId) => {
      await queryClient.cancelQueries({ queryKey: queryListKey });

      queryClient.setQueryData(queryListKey, (old = []) => {
        return old.map((reserve) => (reserve.id === tempReserveId ? newReserve : reserve));
      });
    },
  });

  return mutation;
}

export default useCreateReserve;
