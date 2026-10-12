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
import {
  TS_GENERATION_OPTIONS,
  TS_LAW_OPTIONS,
} from "@/services/api/studies/areas/thermals/constants";
import type { Thermal, ThermalsParams } from "@/services/api/studies/areas/thermals/types";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";

function useCreateThermal({ studyId, areaId }: ThermalsParams) {
  const queryClient = useQueryClient();
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();
  const { t } = useTranslation();

  const { queryKey: queryListKey } = thermalQueries.list(studyId, areaId);

  const mutation = useMutation({
    ...thermalMutations.create(studyId, areaId),
    onMutate: async (variables) => {
      const { values } = variables;
      const tempThermalId = crypto.randomUUID();

      await queryClient.cancelQueries({ queryKey: queryListKey });

      queryClient.setQueryData(queryListKey, (old = []) => {
        return [
          ...old,
          createOptimisticListItem<Thermal>({
            ...values,
            id: tempThermalId,
            group: values.group ?? null,
            enabled: values.enabled ?? false,
            unitCount: values.unitCount ?? 0,
            nominalCapacity: values.nominalCapacity ?? 0,
            mustRun: values.mustRun ?? false,
            minStablePower: values.minStablePower ?? 0,
            spinning: values.spinning ?? 0,
            minUpTime: values.minUpTime ?? 0,
            minDownTime: values.minDownTime ?? 0,
            marginalCost: values.marginalCost ?? 0,
            fixedCost: values.fixedCost ?? 0,
            startupCost: values.startupCost ?? 0,
            marketBidCost: values.marketBidCost ?? 0,
            spreadCost: values.spreadCost ?? 0,
            genTs: values.genTs ?? TS_GENERATION_OPTIONS[0],
            volatilityForced: values.volatilityForced ?? 0,
            volatilityPlanned: values.volatilityPlanned ?? 0,
            lawForced: values.lawForced ?? TS_LAW_OPTIONS[0],
            lawPlanned: values.lawPlanned ?? TS_LAW_OPTIONS[0],
            co2: values.co2 ?? 0,
          }),
        ];
      });

      return tempThermalId;
    },
    onError: (error, variables, tempThermalId) => {
      enqueueErrorSnackbar(
        // TODO i18n
        t("study.modeling.bindingConst.create.error", { name: variables.values.name }),
        error,
      );

      if (!tempThermalId) {
        return;
      }

      queryClient.setQueryData(queryListKey, (old = []) => {
        return old.filter((thermal) => thermal.id !== tempThermalId);
      });
    },
    onSuccess: (newThermal, _, tempThermalId) => {
      queryClient.setQueryData(queryListKey, (old = []) => {
        return old.map((thermal) => (thermal.id === tempThermalId ? newThermal : thermal));
      });
    },
  });

  return mutation;
}

export default useCreateThermal;
