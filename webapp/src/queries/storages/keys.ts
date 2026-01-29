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

import type { StorageParams } from "@/services/api/studies/areas/storages/types";
import type { AreaWithId, StudyMetadata } from "@/types/types";
import { areaKeys } from "../areas/keys";

export const storageKeys = {
  all: () => [...areaKeys.all(), "storages"],
  list: (studyId: StudyMetadata["id"], areaId: AreaWithId["id"]) => {
    return [...storageKeys.all(), { studyId, areaId }];
  },
  allConstraints: () => [...storageKeys.all(), "storageConstraints"],
  constraintList: (
    studyId: StudyMetadata["id"],
    areaId: AreaWithId["id"],
    storageId: StorageParams["storageId"],
  ) => {
    return [...storageKeys.allConstraints(), { studyId, areaId, storageId }];
  },
  createConstraint: (
    studyId: StudyMetadata["id"],
    areaId: AreaWithId["id"],
    storageId: StorageParams["storageId"],
  ) => {
    return [...storageKeys.constraintList(studyId, areaId, storageId), "createStorageConstraint"];
  },
  updateConstraint: (
    studyId: StudyMetadata["id"],
    areaId: AreaWithId["id"],
    storageId: StorageParams["storageId"],
  ) => {
    return [...storageKeys.constraintList(studyId, areaId, storageId), "updateStorageConstraint"];
  },
  deleteConstraint: (
    studyId: StudyMetadata["id"],
    areaId: AreaWithId["id"],
    storageId: StorageParams["storageId"],
  ) => {
    return [...storageKeys.constraintList(studyId, areaId, storageId), "deleteStorageConstraint"];
  },
};
