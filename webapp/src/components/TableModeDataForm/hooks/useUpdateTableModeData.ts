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
import { renewableKeys } from "@/queries/renewables/keys";
import { storageKeys } from "@/queries/storages/keys";
import { thermalKeys } from "@/queries/thermals/keys";
import { setTableModeData } from "@/services/api/studies/tableMode";
import { useMutation, useQueryClient } from "@tanstack/react-query";

const clusterKeys = {
  thermals: thermalKeys,
  renewables: renewableKeys,
  "st-storages": storageKeys,
};

function useUpdateTableModeData() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: setTableModeData,
    onSuccess: async (_, { studyId, tableType, data }) => {
      if (tableType !== "thermals" && tableType !== "renewables" && tableType !== "st-storages") {
        return;
      }

      // Backend row keys are "area / cluster". Refresh each affected area only once.
      const areaIds = new Set(Object.keys(data).map((key) => key.split(" / ")[0]));

      await Promise.all(
        [...areaIds].map((areaId) =>
          invalidateQueriesAfterMutation(queryClient, clusterKeys[tableType].list(studyId, areaId)),
        ),
      );
    },
  });
}

export default useUpdateTableModeData;
