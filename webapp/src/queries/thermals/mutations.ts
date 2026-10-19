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
  createThermalCluster,
  deleteThermalClusters,
  duplicateThermalCluster,
  updateThermalCluster,
} from "@/services/api/studies/areas/thermals";
import type { Study } from "@/services/api/studies/types";
import type { AreaWithId } from "@/types/types";
import { mutationOptions } from "@tanstack/react-query";
import { thermalKeys } from "./keys";

export const thermalMutations = {
  create: (studyId: Study["id"], areaId: AreaWithId["id"]) => {
    return mutationOptions({
      mutationKey: thermalKeys.create(studyId, areaId),
      mutationFn: createThermalCluster,
    });
  },
  update: (studyId: Study["id"], areaId: AreaWithId["id"]) => {
    return mutationOptions({
      mutationKey: thermalKeys.update(studyId, areaId),
      mutationFn: updateThermalCluster,
    });
  },
  duplicate: (studyId: Study["id"], areaId: AreaWithId["id"]) => {
    return mutationOptions({
      mutationKey: thermalKeys.duplicate(studyId, areaId),
      mutationFn: duplicateThermalCluster,
    });
  },
  delete: (studyId: Study["id"], areaId: AreaWithId["id"]) => {
    return mutationOptions({
      mutationKey: thermalKeys.delete(studyId, areaId),
      mutationFn: deleteThermalClusters,
    });
  },
};
