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

import { renewableKeys } from "@/queries/renewables/keys";
import { storageKeys } from "@/queries/storages/keys";
import { tableModeMutations } from "@/queries/tableMode/mutations";
import { thermalKeys } from "@/queries/thermals/keys";
import { setStudySynthesis } from "@/redux/ducks/studySyntheses";
import useAppDispatch from "@/redux/hooks/useAppDispatch";
import { useMutation, useQueryClient } from "@tanstack/react-query";

const clusterKeys = {
  thermals: thermalKeys,
  renewables: renewableKeys,
  "st-storages": storageKeys,
};

function useUpdateTableModeData() {
  const queryClient = useQueryClient();
  const dispatch = useAppDispatch();

  return useMutation({
    ...tableModeMutations.updateData(),
    onSuccess: async (_, { studyId, tableType, data }) => {
      if (tableType !== "thermals" && tableType !== "renewables" && tableType !== "st-storages") {
        return;
      }

      // Backend row keys are "area / cluster". Refresh each affected area only once.
      const areaIds = new Set(Object.keys(data).map((key) => key.split(" / ")[0]));
      if (areaIds.size === 0) {
        return;
      }

      void dispatch(setStudySynthesis(studyId));
      await Promise.all(
        [...areaIds].map((areaId) =>
          queryClient.invalidateQueries({
            queryKey: clusterKeys[tableType].list(studyId, areaId),
          }),
        ),
      );
    },
  });
}

export default useUpdateTableModeData;
