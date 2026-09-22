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

import type { AreaWithId } from "@/types/types";
import type { PartialExceptFor } from "@/utils/tsUtils";
import type { Study } from "../../types";
import type {
  COST_GENERATION_OPTIONS,
  THERMAL_GROUPS,
  TS_GENERATION_OPTIONS,
  TS_LAW_OPTIONS,
} from "./constants";

export type ThermalGroup = (typeof THERMAL_GROUPS)[number];

type LocalTSGenerationBehavior = (typeof TS_GENERATION_OPTIONS)[number];
type TimeSeriesLawOption = (typeof TS_LAW_OPTIONS)[number];
type CostGeneration = (typeof COST_GENERATION_OPTIONS)[number];

// TODO(PR2): reconcile legacy form types with nullable API fields when migrating consumers.
export interface ThermalCluster<LegacyGroup extends boolean = false> {
  id: string;
  name: string;
  group: LegacyGroup extends true ? ThermalGroup : string; // Before v9.3 => ThermalGroup, since v9.3 => string
  enabled: boolean;
  unitCount: number;
  nominalCapacity: number;
  mustRun: boolean;
  minStablePower: number;
  spinning: number;
  minUpTime: number;
  minDownTime: number;
  marginalCost: number;
  fixedCost: number;
  startupCost: number;
  marketBidCost: number;
  spreadCost: number;
  genTs: LocalTSGenerationBehavior;
  volatilityForced: number;
  volatilityPlanned: number;
  lawForced: TimeSeriesLawOption;
  lawPlanned: TimeSeriesLawOption;
  co2: number;
  // Since v8.6
  so2?: number;
  nh3?: number;
  nox?: number;
  nmvoc?: number;
  pm25?: number;
  pm5?: number;
  pm10?: number;
  op1?: number;
  op2?: number;
  op3?: number;
  op4?: number;
  op5?: number;
  // Since v8.7
  costGeneration?: CostGeneration;
  efficiency?: number;
  variableOMCost?: number;
}

export type ThermalClusterCreation = PartialExceptFor<Omit<ThermalCluster, "id">, "name">;
export type ThermalClusterUpdate = Partial<Omit<ThermalCluster, "id" | "name">>;

export interface ThermalsAreaParams {
  studyId: Study["id"];
  areaId: AreaWithId["id"];
}

export interface GetThermalClusterParams extends ThermalsAreaParams {
  clusterId: ThermalCluster["id"];
}

export interface CreateThermalClusterParams extends ThermalsAreaParams {
  values: ThermalClusterCreation;
}

export interface UpdateThermalClusterParams extends GetThermalClusterParams {
  values: ThermalClusterUpdate;
}

export interface DuplicateThermalClusterParams extends GetThermalClusterParams {
  newName: ThermalCluster["name"];
}

export interface DeleteThermalClustersParams extends ThermalsAreaParams {
  clusterIds: Array<ThermalCluster["id"]>;
}
