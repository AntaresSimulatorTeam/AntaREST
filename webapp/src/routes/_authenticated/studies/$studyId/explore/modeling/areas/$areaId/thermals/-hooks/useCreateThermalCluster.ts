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

import { thermalKeys } from "@/queries/thermals/keys";
import { thermalMutations } from "@/queries/thermals/mutations";
import { setStudySynthesis } from "@/redux/ducks/studySyntheses";
import useAppDispatch from "@/redux/hooks/useAppDispatch";
import type { ThermalsAreaParams } from "@/services/api/studies/areas/thermals/types";
import { useMutation, useQueryClient } from "@tanstack/react-query";

function useCreateThermalCluster({ studyId, areaId }: ThermalsAreaParams) {
  const queryClient = useQueryClient();
  const dispatch = useAppDispatch();

  return useMutation({
    ...thermalMutations.create(studyId, areaId),
    onSuccess: async (_, { studyId, areaId }) => {
      void dispatch(setStudySynthesis(studyId));
      // GroupedDataTable owns optimistic rows until its controlled mode is available.
      await queryClient.invalidateQueries({ queryKey: thermalKeys.list(studyId, areaId) });
    },
  });
}

export default useCreateThermalCluster;
