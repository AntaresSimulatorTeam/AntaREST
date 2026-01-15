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

import {
  createStorageConstraint,
  deleteStorageConstraint,
  getStorageConstraints,
} from "@/services/api/studies/areas/storages";
import type { StorageParams } from "@/services/api/studies/areas/storages/types";
import type { AreaWithId, StudyMetadata } from "@/types/types";
import { mutationOptions, queryOptions } from "@tanstack/react-query";
import { areaQueries } from "./areas";
import { queryList } from "./utils";

export const storageQueries = {
  all: () => [...areaQueries.all(), "storages"],
  list: (studyId: StudyMetadata["id"], areaId: AreaWithId["id"]) => {
    return [...storageQueries.all(), { studyId, areaId }];
  },
  allConstraints: () => [...storageQueries.all(), "storageConstraints"],
  constraintList: (
    studyId: StudyMetadata["id"],
    areaId: AreaWithId["id"],
    storageId: StorageParams["storageId"],
  ) => {
    return queryOptions({
      queryKey: [...storageQueries.allConstraints(), { studyId, areaId, storageId }],
      queryFn: async () => queryList(await getStorageConstraints({ studyId, areaId, storageId })),
      refetchOnWindowFocus: (query) => !query.state.data?.some((c) => c.isOptimistic),
      refetchOnReconnect: (query) => !query.state.data?.some((c) => c.isOptimistic),
      refetchOnMount: (query) => !query.state.data?.some((c) => c.isOptimistic),
    });
  },
};

export const storageMutations = {
  constraintList: (
    studyId: StudyMetadata["id"],
    areaId: AreaWithId["id"],
    storageId: StorageParams["storageId"],
  ) => [...storageQueries.allConstraints(), { studyId, areaId, storageId }],
  createConstraint: (
    studyId: StudyMetadata["id"],
    areaId: AreaWithId["id"],
    storageId: StorageParams["storageId"],
  ) => {
    return mutationOptions({
      mutationKey: [
        ...storageMutations.constraintList(studyId, areaId, storageId),
        "createStorageConstraint",
      ],
      mutationFn: createStorageConstraint,
    });
  },
  deleteConstraint: (
    studyId: StudyMetadata["id"],
    areaId: AreaWithId["id"],
    storageId: StorageParams["storageId"],
  ) => {
    return mutationOptions({
      mutationKey: [
        ...storageMutations.constraintList(studyId, areaId, storageId),
        "deleteStorageConstraint",
      ],
      mutationFn: deleteStorageConstraint,
    });
  },
};
