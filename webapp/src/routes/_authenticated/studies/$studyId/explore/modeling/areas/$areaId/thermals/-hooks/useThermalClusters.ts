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

import { thermalQueries } from "@/queries/thermals/queries";
import type {
  ThermalCluster,
  ThermalsAreaParams,
} from "@/services/api/studies/areas/thermals/types";
import { useQuery } from "@tanstack/react-query";
import { adaptThermalClusterToView } from "../-adapters";

const selectClusters = (clusters: ThermalCluster[]) => clusters.map(adaptThermalClusterToView);

function useThermalClusters({ studyId, areaId }: ThermalsAreaParams) {
  return useQuery({
    ...thermalQueries.list(studyId, areaId),
    select: selectClusters,
  });
}

export default useThermalClusters;
