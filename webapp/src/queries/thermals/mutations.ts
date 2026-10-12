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
  createThermal,
  deleteThermals,
  duplicateThermal,
  updateThermal,
} from "@/services/api/studies/areas/thermals";
import type {
  CreateThermalParams,
  DeleteThermalsParams,
  DuplicateThermalParams,
  UpdateThermalParams,
} from "@/services/api/studies/areas/thermals/types";
import type { Study } from "@/services/api/studies/types";
import type { AreaWithId } from "@/types/types";
import { mutationOptions } from "@tanstack/react-query";
import { thermalKeys } from "./keys";

export const thermalMutations = {
  create: (studyId: Study["id"], areaId: AreaWithId["id"]) => {
    return mutationOptions({
      mutationKey: thermalKeys.create(studyId, areaId),
      mutationFn: (params: Omit<CreateThermalParams, "studyId" | "areaId">) =>
        createThermal({ ...params, studyId, areaId }),
    });
  },
  update: (studyId: Study["id"], areaId: AreaWithId["id"]) => {
    return mutationOptions({
      mutationKey: thermalKeys.update(studyId, areaId),
      mutationFn: (params: Omit<UpdateThermalParams, "studyId" | "areaId">) =>
        updateThermal({ ...params, studyId, areaId }),
    });
  },
  duplicate: (studyId: Study["id"], areaId: AreaWithId["id"]) => {
    return mutationOptions({
      mutationKey: thermalKeys.duplicate(studyId, areaId),
      mutationFn: (params: Omit<DuplicateThermalParams, "studyId" | "areaId">) =>
        duplicateThermal({ ...params, studyId, areaId }),
    });
  },
  delete: (studyId: Study["id"], areaId: AreaWithId["id"]) => {
    return mutationOptions({
      mutationKey: thermalKeys.delete(studyId, areaId),
      mutationFn: (params: Omit<DeleteThermalsParams, "studyId" | "areaId">) =>
        deleteThermals({ ...params, studyId, areaId }),
    });
  },
};
