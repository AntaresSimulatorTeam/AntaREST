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
import { invalidateQueriesAfterMutation } from "@/queries/invalidateQueriesAfterMutation";
import { reserveKeys } from "@/queries/reserves/keys";
import { thermalMutations } from "@/queries/thermals/mutations";
import { thermalQueries } from "@/queries/thermals/queries";
import type { ThermalClustersParams } from "@/services/api/studies/areas/thermals/types";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";

function useDeleteThermalClusters({ studyId, areaId }: ThermalClustersParams) {
  const queryClient = useQueryClient();
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();
  const { t } = useTranslation();

  const { queryKey: queryListKey } = thermalQueries.list(studyId, areaId);

  return useMutation({
    ...thermalMutations.delete(studyId, areaId),
    onMutate: async (variables) => {
      const { thermalIds } = variables;

      await queryClient.cancelQueries({ queryKey: queryListKey });

      const prevThermals = queryClient.getQueryData(queryListKey);
      const thermalsToDelete = prevThermals?.filter(({ id }) => thermalIds.includes(id));

      if (thermalsToDelete && thermalsToDelete.length > 0) {
        queryClient.setQueryData(queryListKey, (old = []) => {
          return old.filter((thermal) => !thermalIds.includes(thermal.id));
        });
      }

      return { thermalsToDelete };
    },
    onError: (error, variables, onMutateResult) => {
      const { thermalIds } = variables;
      const { thermalsToDelete } = onMutateResult || {};

      enqueueErrorSnackbar(
        t("study.modeling.clusters.delete.error", {
          count: thermalIds.length,
          names: thermalsToDelete?.map((t) => t.name) || thermalIds,
        }),
        error,
      );

      if (thermalsToDelete) {
        queryClient.setQueryData(queryListKey, (old = []) => [...old, ...thermalsToDelete]);
      }
    },
    onSuccess: async () => {
      await Promise.all([
        invalidateQueriesAfterMutation(
          queryClient,
          reserveKeys.certifications(studyId, areaId, "thermals"),
        ),
        invalidateQueriesAfterMutation(
          queryClient,
          reserveKeys.symmetries(studyId, areaId, "thermals"),
        ),
      ]);
    },
  });
}

export default useDeleteThermalClusters;
