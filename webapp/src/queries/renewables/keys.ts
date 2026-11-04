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

import type { RenewableCluster } from "@/services/api/studies/areas/renewables/types";
import type { Study } from "@/services/api/studies/types";
import type { AreaWithId } from "@/types/types";
import { areaKeys } from "../areas/keys";

export const renewableKeys = {
  all: () => [...areaKeys.all(), "renewables"],
  list: (studyId: Study["id"], areaId: AreaWithId["id"]) => {
    return [...renewableKeys.all(), { studyId, areaId }];
  },
  create: (studyId: Study["id"], areaId: AreaWithId["id"]) => {
    return [...renewableKeys.list(studyId, areaId), "createRenewableCluster"];
  },
  update: (studyId: Study["id"], areaId: AreaWithId["id"], renewableId: RenewableCluster["id"]) => {
    return [...renewableKeys.list(studyId, areaId), "updateRenewableCluster", { renewableId }];
  },
  duplicate: (studyId: Study["id"], areaId: AreaWithId["id"]) => {
    return [...renewableKeys.list(studyId, areaId), "duplicateRenewableCluster"];
  },
  delete: (studyId: Study["id"], areaId: AreaWithId["id"]) => {
    return [...renewableKeys.list(studyId, areaId), "deleteRenewableClusters"];
  },
};
