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
import type { Thermal, ThermalsParams } from "@/services/api/studies/areas/thermals/types";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";
import { DEFAULT_THERMAL_VALUES } from "../-utils";

function useDuplicateThermal({ studyId, areaId }: ThermalsParams) {
  const queryClient = useQueryClient();
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();
  const { t } = useTranslation();

  const { queryKey: queryListKey } = thermalQueries.list(studyId, areaId);

  return useMutation({
    ...thermalMutations.duplicate(studyId, areaId),
    onMutate: async (variables) => {
      const { thermalId: thermalToDuplicateId, newName } = variables;
      const tempThermalId = crypto.randomUUID();

      await queryClient.cancelQueries({ queryKey: queryListKey });

      const prevThermals = queryClient.getQueryData(queryListKey);
      const thermalToDuplicate = prevThermals?.find(({ id }) => id === thermalToDuplicateId);

      queryClient.setQueryData(queryListKey, (old = []) => {
        return [
          ...old,
          createOptimisticListItem<Thermal>({
            ...DEFAULT_THERMAL_VALUES,
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
        t("study.modeling.thermals.duplicate.error", { name: variables.newName }),
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

export default useDuplicateThermal;
