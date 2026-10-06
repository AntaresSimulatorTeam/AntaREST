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

import { invalidateQueriesAfterMutation } from "@/queries/invalidateQueriesAfterMutation";
import { thermalMutations } from "@/queries/thermals/mutations";
import { thermalQueries } from "@/queries/thermals/queries";
import type { ThermalsAreaParams } from "@/services/api/studies/areas/thermals/types";
import { useMutation, useQueryClient } from "@tanstack/react-query";

function useCreateThermalCluster({ studyId, areaId }: ThermalsAreaParams) {
  const queryClient = useQueryClient();

  return useMutation({
    ...thermalMutations.create(studyId, areaId),
    onSuccess: async (createdCluster, { studyId, areaId }) => {
      const { queryKey } = thermalQueries.list(studyId, areaId);

      // A single cluster response cannot populate a list that has not loaded yet.
      if (!queryClient.getQueryData(queryKey)) {
        await invalidateQueriesAfterMutation(queryClient, queryKey);
        return;
      }

      // An older read must not overwrite the saved cluster.
      await queryClient.cancelQueries({ queryKey });

      queryClient.setQueryData(queryKey, (clusters) => {
        if (!clusters || clusters.some(({ id }) => id === createdCluster.id)) {
          return clusters;
        }

        return [...clusters, createdCluster];
      });
    },
  });
}

export default useCreateThermalCluster;
