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

import { getStorages } from "@/routes/_authenticated/studies/$studyId/explore/modeling/areas/$areaId/storages/-utils";
import { getStorageConstraints } from "@/services/api/studies/areas/storages";
import type { StorageParams } from "@/services/api/studies/areas/storages/types";
import type { AreaWithId, StudyMetadata } from "@/types/types";
import { queryOptions } from "@tanstack/react-query";
import { EXTERNALLY_MUTATED, queryListOptions } from "../utils";
import { storageKeys } from "./keys";

export const storageQueries = {
  list: (studyId: StudyMetadata["id"], areaId: AreaWithId["id"]) => {
    return queryOptions({
      queryKey: storageKeys.list(studyId, areaId),
      queryFn: () => getStorages(studyId, areaId),
      // Storages are mutated by the legacy Storages pages and table mode, none of
      // which invalidate this cache.
      ...EXTERNALLY_MUTATED,
    });
  },
  constraintList: (
    studyId: StudyMetadata["id"],
    areaId: AreaWithId["id"],
    storageId: StorageParams["storageId"],
  ) => {
    return queryListOptions({
      queryKey: storageKeys.constraintList(studyId, areaId, storageId),
      queryFn: () => getStorageConstraints({ studyId, areaId, storageId }),
    });
  },
};
