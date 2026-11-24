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
import { renewableMutations } from "@/queries/renewables/mutations";
import { renewableQueries } from "@/queries/renewables/queries";
import type { RenewableClustersParams } from "@/services/api/studies/areas/renewables/types";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";

function useDeleteRenewableClusters({ studyId, areaId }: RenewableClustersParams) {
  const queryClient = useQueryClient();
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();
  const { t } = useTranslation();

  const { queryKey: queryListKey } = renewableQueries.list(studyId, areaId);

  return useMutation({
    ...renewableMutations.delete(studyId, areaId),
    onMutate: async (variables) => {
      const { renewableIds } = variables;

      await queryClient.cancelQueries({ queryKey: queryListKey });

      const prevRenewables = queryClient.getQueryData(queryListKey);
      const renewablesToDelete = prevRenewables?.filter(({ id }) => renewableIds.includes(id));

      if (renewablesToDelete && renewablesToDelete.length > 0) {
        queryClient.setQueryData(queryListKey, (old = []) => {
          return old.filter((renewable) => !renewableIds.includes(renewable.id));
        });
      }

      return { renewablesToDelete };
    },
    onError: (error, variables, onMutateResult) => {
      const { renewableIds } = variables;
      const { renewablesToDelete } = onMutateResult || {};

      enqueueErrorSnackbar(
        t("study.modeling.clusters.delete.error", {
          count: renewableIds.length,
          names: renewablesToDelete?.map((t) => t.name) || renewableIds,
        }),
        error,
      );

      if (renewablesToDelete) {
        queryClient.setQueryData(queryListKey, (old = []) => [...old, ...renewablesToDelete]);
      }
    },
  });
}

export default useDeleteRenewableClusters;
