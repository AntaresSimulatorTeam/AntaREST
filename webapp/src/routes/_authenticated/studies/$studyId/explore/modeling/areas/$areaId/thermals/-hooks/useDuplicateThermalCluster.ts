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
import { thermalKeys } from "@/queries/thermals/keys";
import { thermalMutations } from "@/queries/thermals/mutations";
import type { ThermalsAreaParams } from "@/services/api/studies/areas/thermals/types";
import { useMutation, useQueryClient } from "@tanstack/react-query";

function useDuplicateThermalCluster({ studyId, areaId }: ThermalsAreaParams) {
  const queryClient = useQueryClient();

  return useMutation({
    ...thermalMutations.duplicate(studyId, areaId),
    onSuccess: async (_, { studyId, areaId }) => {
      // GroupedDataTable owns optimistic rows until its controlled mode is available.
      await invalidateQueriesAfterMutation(queryClient, thermalKeys.list(studyId, areaId));
    },
  });
}

export default useDuplicateThermalCluster;
