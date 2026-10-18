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
  createRenewableCluster,
  deleteRenewableClusters,
  duplicateRenewableCluster,
  updateRenewableCluster,
} from "@/services/api/studies/areas/renewables";
import type {
  CreateRenewableClusterParams,
  DeleteRenewableClustersParams,
  DuplicateRenewableClusterParams,
  UpdateRenewableClusterParams,
} from "@/services/api/studies/areas/renewables/types";
import type { Study } from "@/services/api/studies/types";
import type { AreaWithId } from "@/types/types";
import { mutationOptions } from "@tanstack/react-query";
import { renewableKeys } from "./keys";

export const renewableMutations = {
  create: (studyId: Study["id"], areaId: AreaWithId["id"]) => {
    return mutationOptions({
      mutationKey: renewableKeys.create(studyId, areaId),
      mutationFn: (params: Omit<CreateRenewableClusterParams, "studyId" | "areaId">) => {
        return createRenewableCluster({ ...params, studyId, areaId });
      },
    });
  },
  update: (studyId: Study["id"], areaId: AreaWithId["id"]) => {
    return mutationOptions({
      mutationKey: renewableKeys.update(studyId, areaId),
      mutationFn: (params: Omit<UpdateRenewableClusterParams, "studyId" | "areaId">) => {
        return updateRenewableCluster({ ...params, studyId, areaId });
      },
    });
  },
  duplicate: (studyId: Study["id"], areaId: AreaWithId["id"]) => {
    return mutationOptions({
      mutationKey: renewableKeys.duplicate(studyId, areaId),
      mutationFn: (params: Omit<DuplicateRenewableClusterParams, "studyId" | "areaId">) => {
        return duplicateRenewableCluster({ ...params, studyId, areaId });
      },
    });
  },
  delete: (studyId: Study["id"], areaId: AreaWithId["id"]) => {
    return mutationOptions({
      mutationKey: renewableKeys.delete(studyId, areaId),
      mutationFn: (params: Omit<DeleteRenewableClustersParams, "studyId" | "areaId">) => {
        return deleteRenewableClusters({ ...params, studyId, areaId });
      },
    });
  },
};
