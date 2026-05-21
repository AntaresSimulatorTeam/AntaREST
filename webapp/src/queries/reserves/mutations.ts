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
  createReserve,
  deleteReserves,
  updateReserve,
  updateReserveGlobalParameters,
} from "@/services/api/studies/areas/reserves";
import type { AreaWithId, StudyMetadata } from "@/types/types";
import { mutationOptions } from "@tanstack/react-query";
import { reserveKeys } from "./keys";

export const reserveMutations = {
  create: (studyId: StudyMetadata["id"], areaId: AreaWithId["id"]) => {
    return mutationOptions({
      mutationKey: reserveKeys.create(studyId, areaId),
      mutationFn: createReserve,
    });
  },
  update: (studyId: StudyMetadata["id"], areaId: AreaWithId["id"]) => {
    return mutationOptions({
      mutationKey: reserveKeys.update(studyId, areaId),
      mutationFn: updateReserve,
    });
  },
  delete: (studyId: StudyMetadata["id"], areaId: AreaWithId["id"]) => {
    return mutationOptions({
      mutationKey: reserveKeys.delete(studyId, areaId),
      mutationFn: deleteReserves,
    });
  },
  updateGlobalParameters: (studyId: StudyMetadata["id"], areaId: AreaWithId["id"]) => {
    return mutationOptions({
      mutationKey: reserveKeys.updateGlobalParameters(studyId, areaId),
      mutationFn: updateReserveGlobalParameters,
    });
  },
};
