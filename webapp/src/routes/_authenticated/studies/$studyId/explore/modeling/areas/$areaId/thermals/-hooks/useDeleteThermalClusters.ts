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
import type { ThermalsAreaParams } from "@/services/api/studies/areas/thermals/types";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";

function useDeleteThermalClusters({ studyId, areaId }: ThermalsAreaParams) {
  const queryClient = useQueryClient();
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();
  const { t } = useTranslation();

  const { queryKey: queryListKey } = thermalQueries.list(studyId, areaId);

  return useMutation({
    ...thermalMutations.delete(studyId, areaId),
    onMutate: async (variables) => {
      const { clusterIds } = variables;

      await queryClient.cancelQueries({ queryKey: queryListKey });

      const prevThermals = queryClient.getQueryData(queryListKey);
      const thermalsToDelete = prevThermals?.filter(({ id }) => clusterIds.includes(id));

      if (thermalsToDelete && thermalsToDelete.length > 0) {
        queryClient.setQueryData(queryListKey, (old = []) => {
          return old.filter((thermal) => !clusterIds.includes(thermal.id));
        });
      }

      return { thermalsToDelete };
    },
    onError: (error, variables, onMutateResult) => {
      const { clusterIds } = variables;
      const { thermalsToDelete } = onMutateResult || {};

      enqueueErrorSnackbar(
        // TODO i18n
        t("study.modeling.bindingConst.deleteBindingConstraint.error", {
          name: thermalsToDelete?.map((t) => t.name) || clusterIds,
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
