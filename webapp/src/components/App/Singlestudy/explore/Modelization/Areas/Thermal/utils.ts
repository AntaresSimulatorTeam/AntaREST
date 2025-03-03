/**
 * Copyright (c) 2025, RTE (https://www.rte-france.com)
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

import type { Area, Cluster, StudyMetadata } from "../../../../../../../types/types";
import client from "../../../../../../../services/api/client";
import type { PartialExceptFor } from "../../../../../../../utils/tsUtils";
import type { ClusterWithCapacity } from "../common/clustersUtils";

////////////////////////////////////////////////////////////////
// Constants
////////////////////////////////////////////////////////////////

export const COMMON_MATRIX_COLS = [
  "Marginal cost modulation",
  "Market bid modulation",
  "Capacity modulation",
  "Min gen modulation",
] as const;

export const TS_GEN_MATRIX_COLS = [
  "FO Duration",
  "PO Duration",
  "FO Rate",
  "PO Rate",
  "NPO Min",
  "NPO Max",
] as const;

export const THERMAL_GROUPS = [
  "gas",
  "hard coal",
  "lignite",
  "mixed fuel",
  "nuclear",
  "oil",
  "other 1",
  "other 2",
  "other 3",
  "other 4",
] as const;

export const THERMAL_POLLUTANTS = [
  "co2",
  // Since v8.6
  "so2",
  "nh3",
  "nox",
  "nmvoc",
  "pm25",
  "pm5",
  "pm10",
  "op1",
  "op2",
  "op3",
  "op4",
  "op5",
] as const;

export const TS_GENERATION_OPTIONS = [
  "use global",
  "force no generation",
  "force generation",
] as const;

export const TS_LAW_OPTIONS = ["geometric", "uniform"] as const;

export const COST_GENERATION_OPTIONS = ["SetManually", "useCostTimeseries"] as const;

////////////////////////////////////////////////////////////////
// Types
////////////////////////////////////////////////////////////////

export type ThermalGroup = (typeof THERMAL_GROUPS)[number];

type LocalTSGenerationBehavior = (typeof TS_GENERATION_OPTIONS)[number];
type TimeSeriesLawOption = (typeof TS_LAW_OPTIONS)[number];
type CostGeneration = (typeof COST_GENERATION_OPTIONS)[number];
type ThermalPollutants = Record<(typeof THERMAL_POLLUTANTS)[number], number>;

export interface ThermalCluster extends ThermalPollutants {
  id: string;
  name: string;
  group: ThermalGroup;
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
  // Since v8.7
  costGeneration: CostGeneration;
  efficiency: number;
  variableOMCost: number;
}

export type ThermalClusterWithCapacity = ClusterWithCapacity<ThermalCluster>;

////////////////////////////////////////////////////////////////
// Functions
////////////////////////////////////////////////////////////////

const getClustersUrl = (studyId: StudyMetadata["id"], areaId: Area["name"]): string =>
  `/v1/studies/${studyId}/areas/${areaId}/clusters/thermal`;

const getClusterUrl = (
  studyId: StudyMetadata["id"],
  areaId: Area["name"],
  clusterId: Cluster["id"],
): string => `${getClustersUrl(studyId, areaId)}/${clusterId}`;

////////////////////////////////////////////////////////////////
// API
////////////////////////////////////////////////////////////////

export async function getThermalClusters(studyId: StudyMetadata["id"], areaId: Area["name"]) {
  const res = await client.get<ThermalCluster[]>(getClustersUrl(studyId, areaId));
  return res.data;
}

export async function getThermalCluster(
  studyId: StudyMetadata["id"],
  areaId: Area["name"],
  clusterId: Cluster["id"],
) {
  const res = await client.get<ThermalCluster>(getClusterUrl(studyId, areaId, clusterId));
  return res.data;
}

export async function updateThermalCluster(
  studyId: StudyMetadata["id"],
  areaId: Area["name"],
  clusterId: Cluster["id"],
  data: Partial<ThermalCluster>,
) {
  const res = await client.patch<ThermalCluster>(getClusterUrl(studyId, areaId, clusterId), data);
  return res.data;
}

export async function createThermalCluster(
  studyId: StudyMetadata["id"],
  areaId: Area["name"],
  data: PartialExceptFor<ThermalCluster, "name">,
) {
  const res = await client.post<ThermalCluster>(getClustersUrl(studyId, areaId), data);
  return res.data;
}

export async function duplicateThermalCluster(
  studyId: StudyMetadata["id"],
  areaId: Area["name"],
  sourceClusterId: ThermalCluster["id"],
  newName: ThermalCluster["name"],
) {
  const res = await client.post<ThermalCluster>(
    `/v1/studies/${studyId}/areas/${areaId}/thermals/${sourceClusterId}`,
    null,
    { params: { newName } },
  );
  return res.data;
}

export async function deleteThermalClusters(
  studyId: StudyMetadata["id"],
  areaId: Area["name"],
  clusterIds: Array<Cluster["id"]>,
) {
  await client.delete(getClustersUrl(studyId, areaId), { data: clusterIds });
}
