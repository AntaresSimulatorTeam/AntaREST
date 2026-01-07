/**
 * Copyright (c) 2025, RTE (https://www.rte-france.com)
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
import { areaKeys } from "./areas";
import { queryList } from "./utils";

export const storageQueries = {
  all: () => [...areaKeys.all, "storages"],
  list: (studyId: StudyMetadata["id"], areaId: AreaWithId["id"]) => {
    return [...storageQueries.all(), { studyId, areaId }];
  },
  constraintList: (
    studyId: StudyMetadata["id"],
    areaId: AreaWithId["id"],
    storageId: StorageParams["storageId"],
  ) => {
    return queryOptions({
      queryKey: [...storageQueries.all(), "constraints", { studyId, areaId, storageId }],
      queryFn: async () => {
        return queryList(await getStorageConstraints({ studyId, areaId, storageId }));
      },
    });
  },
};

export const storageMutations = {
  createConstraint: () => {
    return mutationOptions({
      mutationKey: ["createStorageConstraint"],
      mutationFn: createStorageConstraint,
    });
  },
  deleteConstraint: () => {
    return mutationOptions({
      mutationKey: ["deleteStorageConstraint"],
      mutationFn: deleteStorageConstraint,
    });
  },
};
