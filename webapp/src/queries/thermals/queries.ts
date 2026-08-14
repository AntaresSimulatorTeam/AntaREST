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

import { getThermalClusters } from "@/routes/_authenticated/studies/$studyId/explore/modeling/areas/$areaId/thermals/-utils";
import type { Study } from "@/services/api/studies/types";
import type { AreaWithId } from "@/types/types";
import { queryOptions } from "@tanstack/react-query";
import { EXTERNALLY_MUTATED } from "../utils";
import { thermalKeys } from "./keys";

export const thermalQueries = {
  list: (studyId: Study["id"], areaId: AreaWithId["id"]) => {
    return queryOptions({
      queryKey: thermalKeys.list(studyId, areaId),
      queryFn: () => getThermalClusters(studyId, areaId),
      // Clusters are mutated by the legacy Thermals pages and table mode, none of
      // which invalidate this cache.
      ...EXTERNALLY_MUTATED,
    });
  },
};
