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
  updateStorageConstraint,
} from "@/services/api/studies/areas/storages";
import type { StorageParams } from "@/services/api/studies/areas/storages/types";
import type { AreaWithId, StudyMetadata } from "@/types/types";
import { mutationOptions } from "@tanstack/react-query";
import { storageKeys } from "./keys";

export const storageMutations = {
  createConstraint: (
    studyId: StudyMetadata["id"],
    areaId: AreaWithId["id"],
    storageId: StorageParams["storageId"],
  ) => {
    return mutationOptions({
      mutationKey: storageKeys.createConstraint(studyId, areaId, storageId),
      mutationFn: createStorageConstraint,
    });
  },
  updateConstraint: (
    studyId: StudyMetadata["id"],
    areaId: AreaWithId["id"],
    storageId: StorageParams["storageId"],
  ) => {
    return mutationOptions({
      mutationKey: storageKeys.updateConstraint(studyId, areaId, storageId),
      mutationFn: updateStorageConstraint,
    });
  },
  deleteConstraint: (
    studyId: StudyMetadata["id"],
    areaId: AreaWithId["id"],
    storageId: StorageParams["storageId"],
  ) => {
    return mutationOptions({
      mutationKey: storageKeys.deleteConstraint(studyId, areaId, storageId),
      mutationFn: deleteStorageConstraint,
    });
  },
};
