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

import type { Study } from "@/services/api/studies/types";
import type { AreaWithId } from "@/types/types";
import { areaKeys } from "../areas/keys";

export const thermalKeys = {
  all: () => [...areaKeys.all(), "thermals"],
  list: (studyId: Study["id"], areaId: AreaWithId["id"]) => {
    return [...thermalKeys.all(), { studyId, areaId }];
  },
  create: (studyId: Study["id"], areaId: AreaWithId["id"]) => {
    return [...thermalKeys.list(studyId, areaId), "createThermalCluster"];
  },
  update: (studyId: Study["id"], areaId: AreaWithId["id"]) => {
    return [...thermalKeys.list(studyId, areaId), "updateThermalCluster"];
  },
  duplicate: (studyId: Study["id"], areaId: AreaWithId["id"]) => {
    return [...thermalKeys.list(studyId, areaId), "duplicateThermalCluster"];
  },
  delete: (studyId: Study["id"], areaId: AreaWithId["id"]) => {
    return [...thermalKeys.list(studyId, areaId), "deleteThermalClusters"];
  },
};
