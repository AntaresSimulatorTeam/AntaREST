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
  getReserve,
  getReserveGlobalParameters,
  getReserves,
} from "@/services/api/studies/areas/reserves";
import type { Reserve } from "@/services/api/studies/areas/reserves/types";
import type { AreaWithId } from "@/types/types";
import { queryOptions } from "@tanstack/react-query";
import { queryListOptions } from "../utils";
import { reserveKeys } from "./keys";
import type { Study } from "@/services/api/studies/types";

export const reserveQueries = {
  list: (studyId: Study["id"], areaId: AreaWithId["id"]) => {
    return queryListOptions({
      queryKey: reserveKeys.list(studyId, areaId),
      queryFn: () => getReserves({ studyId, areaId }),
    });
  },
  detail: (studyId: Study["id"], areaId: AreaWithId["id"], reserveId: Reserve["id"]) => {
    return queryOptions({
      queryKey: reserveKeys.detail(studyId, areaId, reserveId),
      queryFn: () => getReserve({ studyId, areaId, reserveId }),
    });
  },
  globalParameters: (studyId: Study["id"], areaId: AreaWithId["id"]) => {
    return queryOptions({
      queryKey: reserveKeys.globalParameters(studyId, areaId),
      queryFn: () => getReserveGlobalParameters({ studyId, areaId }),
    });
  },
};
