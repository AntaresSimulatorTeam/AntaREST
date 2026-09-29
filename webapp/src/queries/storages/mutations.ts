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
  createStorage,
  createStorageConstraint,
  deleteStorageConstraint,
  deleteStorages,
  duplicateStorage,
  updateStorage,
  updateStorageConstraint,
} from "@/services/api/studies/areas/storages";
import type { StorageParams } from "@/services/api/studies/areas/storages/types";
import type { AreaWithId } from "@/types/types";
import { mutationOptions } from "@tanstack/react-query";
import { storageKeys } from "./keys";
import type { Study } from "@/services/api/studies/types";

export const storageMutations = {
  create: (studyId: Study["id"], areaId: AreaWithId["id"]) => {
    return mutationOptions({
      mutationKey: storageKeys.create(studyId, areaId),
      mutationFn: createStorage,
    });
  },
  update: (studyId: Study["id"], areaId: AreaWithId["id"]) => {
    return mutationOptions({
      mutationKey: storageKeys.update(studyId, areaId),
      mutationFn: updateStorage,
    });
  },
  duplicate: (studyId: Study["id"], areaId: AreaWithId["id"]) => {
    return mutationOptions({
      mutationKey: storageKeys.duplicate(studyId, areaId),
      mutationFn: duplicateStorage,
    });
  },
  delete: (studyId: Study["id"], areaId: AreaWithId["id"]) => {
    return mutationOptions({
      mutationKey: storageKeys.delete(studyId, areaId),
      mutationFn: deleteStorages,
    });
  },
  createConstraint: (
    studyId: Study["id"],
    areaId: AreaWithId["id"],
    storageId: StorageParams["storageId"],
  ) => {
    return mutationOptions({
      mutationKey: storageKeys.createConstraint(studyId, areaId, storageId),
      mutationFn: createStorageConstraint,
    });
  },
  updateConstraint: (
    studyId: Study["id"],
    areaId: AreaWithId["id"],
    storageId: StorageParams["storageId"],
  ) => {
    return mutationOptions({
      mutationKey: storageKeys.updateConstraint(studyId, areaId, storageId),
      mutationFn: updateStorageConstraint,
    });
  },
  deleteConstraint: (
    studyId: Study["id"],
    areaId: AreaWithId["id"],
    storageId: StorageParams["storageId"],
  ) => {
    return mutationOptions({
      mutationKey: storageKeys.deleteConstraint(studyId, areaId, storageId),
      mutationFn: deleteStorageConstraint,
    });
  },
};
