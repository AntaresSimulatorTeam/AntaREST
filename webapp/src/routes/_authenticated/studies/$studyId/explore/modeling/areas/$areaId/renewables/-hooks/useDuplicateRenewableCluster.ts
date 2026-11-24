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
import { createOptimisticListItem } from "@/queries/utils";
import type {
  RenewableCluster,
  RenewableClustersParams,
} from "@/services/api/studies/areas/renewables/types";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";
import { DEFAULT_RENEWABLE_VALUES } from "../-constants";

function useDuplicateRenewableCluster({ studyId, areaId }: RenewableClustersParams) {
  const queryClient = useQueryClient();
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();
  const { t } = useTranslation();

  const { queryKey: queryListKey } = renewableQueries.list(studyId, areaId);

  return useMutation({
    ...renewableMutations.duplicate(studyId, areaId),
    onMutate: async (variables) => {
      const { renewableId: renewableToDuplicateId, newName } = variables;
      const tempRenewableId = crypto.randomUUID();

      await queryClient.cancelQueries({ queryKey: queryListKey });

      const prevRenewables = queryClient.getQueryData(queryListKey);
      const renewableToDuplicate = prevRenewables?.find(({ id }) => id === renewableToDuplicateId);

      queryClient.setQueryData(queryListKey, (old = []) => {
        return [
          ...old,
          createOptimisticListItem<RenewableCluster>({
            ...DEFAULT_RENEWABLE_VALUES,
            ...renewableToDuplicate,
            id: tempRenewableId,
            name: newName,
          }),
        ];
      });

      return tempRenewableId;
    },
    onError: (error, variables, tempRenewableId) => {
      enqueueErrorSnackbar(
        t("study.modeling.clusters.duplicate.error", { name: variables.newName }),
        error,
      );

      if (!tempRenewableId) {
        return;
      }

      queryClient.setQueryData(queryListKey, (old = []) => {
        return old.filter((renewable) => renewable.id !== tempRenewableId);
      });
    },
    onSuccess: async (duplicatedRenewable, _, tempRenewableId) => {
      await queryClient.cancelQueries({ queryKey: queryListKey });
      queryClient.setQueryData(queryListKey, (old = []) => {
        return old.map((renewable) =>
          renewable.id === tempRenewableId ? duplicatedRenewable : renewable,
        );
      });
    },
  });
}

export default useDuplicateRenewableCluster;
