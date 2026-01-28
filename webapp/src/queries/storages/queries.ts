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

import { getStorageConstraints } from "@/services/api/studies/areas/storages";
import type { StorageParams } from "@/services/api/studies/areas/storages/types";
import type { AreaWithId, StudyMetadata } from "@/types/types";
import { queryOptions } from "@tanstack/react-query";
import { isQueryListMutating, queryList } from "../utils";
import { storageKeys } from "./keys";

export const storageQueries = {
  constraintList: (
    studyId: StudyMetadata["id"],
    areaId: AreaWithId["id"],
    storageId: StorageParams["storageId"],
  ) => {
    return queryOptions({
      queryKey: storageKeys.constraintList(studyId, areaId, storageId),
      queryFn: async () => queryList(await getStorageConstraints({ studyId, areaId, storageId })),
      refetchOnWindowFocus: (query) => !query.state.data || !isQueryListMutating(query.state.data),
      refetchOnReconnect: (query) => !query.state.data || !isQueryListMutating(query.state.data),
      refetchOnMount: (query) => !query.state.data || !isQueryListMutating(query.state.data),
    });
  },
};
