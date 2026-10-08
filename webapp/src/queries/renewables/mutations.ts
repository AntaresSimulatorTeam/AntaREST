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
import type { Study } from "@/services/api/studies/types";
import type { AreaWithId } from "@/types/types";
import { mutationOptions } from "@tanstack/react-query";
import { renewableKeys } from "./keys";

export const renewableMutations = {
  create: (studyId: Study["id"], areaId: AreaWithId["id"]) => {
    return mutationOptions({
      mutationKey: renewableKeys.create(studyId, areaId),
      mutationFn: createRenewableCluster,
    });
  },
  update: (studyId: Study["id"], areaId: AreaWithId["id"]) => {
    return mutationOptions({
      mutationKey: renewableKeys.update(studyId, areaId),
      mutationFn: updateRenewableCluster,
    });
  },
  duplicate: (studyId: Study["id"], areaId: AreaWithId["id"]) => {
    return mutationOptions({
      mutationKey: renewableKeys.duplicate(studyId, areaId),
      mutationFn: duplicateRenewableCluster,
    });
  },
  delete: (studyId: Study["id"], areaId: AreaWithId["id"]) => {
    return mutationOptions({
      mutationKey: renewableKeys.delete(studyId, areaId),
      mutationFn: deleteRenewableClusters,
    });
  },
};
