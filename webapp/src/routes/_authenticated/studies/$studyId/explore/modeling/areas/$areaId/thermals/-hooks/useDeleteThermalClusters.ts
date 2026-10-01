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

import { reserveKeys } from "@/queries/reserves/keys";
import { invalidateQueriesAfterMutation } from "@/queries/invalidateQueriesAfterMutation";
import { thermalKeys } from "@/queries/thermals/keys";
import { thermalMutations } from "@/queries/thermals/mutations";
import type { ThermalsAreaParams } from "@/services/api/studies/areas/thermals/types";
import { useMutation, useQueryClient } from "@tanstack/react-query";

function useDeleteThermalClusters({ studyId, areaId }: ThermalsAreaParams) {
  const queryClient = useQueryClient();

  return useMutation({
    ...thermalMutations.delete(studyId, areaId),
    onSuccess: async (_, { studyId, areaId }) => {
      // GroupedDataTable owns optimistic rows until its controlled mode is available.
      await Promise.all([
        invalidateQueriesAfterMutation(queryClient, thermalKeys.list(studyId, areaId)),
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
