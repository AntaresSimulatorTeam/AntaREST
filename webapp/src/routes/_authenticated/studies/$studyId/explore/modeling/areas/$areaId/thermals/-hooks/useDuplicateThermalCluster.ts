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
import { thermalMutations } from "@/queries/thermals/mutations";
import { thermalQueries } from "@/queries/thermals/queries";
import { createOptimisticListItem } from "@/queries/utils";
import type {
  ThermalCluster,
  ThermalsAreaParams,
} from "@/services/api/studies/areas/thermals/types";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";
import { TS_GENERATION_OPTIONS, TS_LAW_OPTIONS } from "../-utils";

function useDuplicateThermalCluster({ studyId, areaId }: ThermalsAreaParams) {
  const queryClient = useQueryClient();
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();
  const { t } = useTranslation();

  const { queryKey: queryListKey } = thermalQueries.list(studyId, areaId);

  return useMutation({
    ...thermalMutations.duplicate(studyId, areaId),
    onMutate: async (variables) => {
      const { clusterId: thermalToDuplicateId, newName } = variables;
      const tempThermalId = crypto.randomUUID();

      await queryClient.cancelQueries({ queryKey: queryListKey });

      const prevThermals = queryClient.getQueryData(queryListKey);
      const thermalToDuplicate = prevThermals?.find(({ id }) => id === thermalToDuplicateId);

      queryClient.setQueryData(queryListKey, (old = []) => {
        return [
          ...old,
          createOptimisticListItem<ThermalCluster>({
            group: null,
            enabled: false,
            unitCount: 0,
            nominalCapacity: 0,
            mustRun: false,
            minStablePower: 0,
            spinning: 0,
            minUpTime: 0,
            minDownTime: 0,
            marginalCost: 0,
            fixedCost: 0,
            startupCost: 0,
            marketBidCost: 0,
            spreadCost: 0,
            genTs: TS_GENERATION_OPTIONS[0],
            volatilityForced: 0,
            volatilityPlanned: 0,
            lawForced: TS_LAW_OPTIONS[0],
            lawPlanned: TS_LAW_OPTIONS[0],
            co2: 0,
            ...thermalToDuplicate,
            id: tempThermalId,
            name: newName,
          }),
        ];
      });

      return tempThermalId;
    },
    onError: (error, variables, tempThermalId) => {
      enqueueErrorSnackbar(
        // TODO i18n
        t("study.modeling.bindingConst.duplicate.error", { name: variables.newName }),
        error,
      );

      if (!tempThermalId) {
        return;
      }

      queryClient.setQueryData(queryListKey, (old = []) => {
        return old.filter((thermal) => thermal.id !== tempThermalId);
      });
    },
    onSuccess: (duplicatedThermal, _, tempThermalId) => {
      queryClient.setQueryData(queryListKey, (old = []) => {
        return old.map((thermal) => (thermal.id === tempThermalId ? duplicatedThermal : thermal));
      });
    },
  });
}

export default useDuplicateThermalCluster;
