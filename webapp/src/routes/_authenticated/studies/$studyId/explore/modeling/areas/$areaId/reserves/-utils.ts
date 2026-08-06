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

import { areaKeys } from "@/queries/areas/keys";
import type { Study } from "@/services/api/studies/types";
import type { AreaWithId } from "@/types/types";
import { queryOptions } from "@tanstack/react-query";
import { getThermalClusters } from "../thermals/-utils";

// Thermal clusters have no query layer yet (their API service still lives in the
// thermals route folder), so the query options are defined here for now.
export const thermalClustersQueries = {
  list: (studyId: Study["id"], areaId: AreaWithId["id"]) => {
    return queryOptions({
      queryKey: [...areaKeys.all(), "thermals", { studyId, areaId }],
      queryFn: () => getThermalClusters(studyId, areaId),
    });
  },
};
