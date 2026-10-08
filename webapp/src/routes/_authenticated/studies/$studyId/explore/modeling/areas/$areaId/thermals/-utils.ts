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

import type { ClusterWithCapacity } from "@/routes/_authenticated/studies/$studyId/explore/modeling/areas/$areaId/-clustersUtils";
import { adaptThermalClusterToView } from "./-adapters";

export {
  COST_GENERATION_OPTIONS,
  THERMAL_GROUPS,
  TS_GENERATION_OPTIONS,
  TS_LAW_OPTIONS,
} from "@/services/api/studies/areas/thermals/constants";
export type { ThermalGroup } from "@/services/api/studies/areas/thermals/types";
export { COMMON_MATRIX_COLS, THERMAL_POLLUTANTS, TS_GEN_MATRIX_COLS } from "./-constants";

export type ThermalCluster = ReturnType<typeof adaptThermalClusterToView>;
export type ThermalClusterWithCapacity = ClusterWithCapacity<ThermalCluster>;
