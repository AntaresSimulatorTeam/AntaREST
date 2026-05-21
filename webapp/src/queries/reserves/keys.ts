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

import type { Reserve } from "@/services/api/studies/areas/reserves/types";
import type { AreaWithId, StudyMetadata } from "@/types/types";
import { areaKeys } from "../areas/keys";

export const reserveKeys = {
  all: () => [...areaKeys.all(), "reserves"],
  list: (studyId: StudyMetadata["id"], areaId: AreaWithId["id"]) => {
    return [...reserveKeys.all(), { studyId, areaId }];
  },
  detail: (studyId: StudyMetadata["id"], areaId: AreaWithId["id"], reserveId: Reserve["id"]) => {
    return [...reserveKeys.list(studyId, areaId), reserveId];
  },
  globalParameters: (studyId: StudyMetadata["id"], areaId: AreaWithId["id"]) => {
    return [...reserveKeys.all(), "globalParameters", { studyId, areaId }];
  },
  create: (studyId: StudyMetadata["id"], areaId: AreaWithId["id"]) => {
    return [...reserveKeys.list(studyId, areaId), "createReserve"];
  },
  update: (studyId: StudyMetadata["id"], areaId: AreaWithId["id"]) => {
    return [...reserveKeys.list(studyId, areaId), "updateReserve"];
  },
  delete: (studyId: StudyMetadata["id"], areaId: AreaWithId["id"]) => {
    return [...reserveKeys.list(studyId, areaId), "deleteReserves"];
  },
  updateGlobalParameters: (studyId: StudyMetadata["id"], areaId: AreaWithId["id"]) => {
    return [...reserveKeys.globalParameters(studyId, areaId), "updateReserveGlobalParameters"];
  },
};
