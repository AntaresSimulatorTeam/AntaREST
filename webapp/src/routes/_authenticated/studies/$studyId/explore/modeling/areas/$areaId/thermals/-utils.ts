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
import * as thermalApi from "@/services/api/studies/areas/thermals";
import type { Area, Cluster, StudyMetadata } from "@/types/types";
import type { PartialExceptFor } from "@/utils/tsUtils";
import { adaptThermalClusterToView } from "./-adapters";

// TODO(PR2): remove compatibility exports and wrappers once consumers use the Thermal data layer.
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

export async function getThermalClusters(studyId: StudyMetadata["id"], areaId: Area["name"]) {
  const clusters = await thermalApi.getThermalClusters({ studyId, areaId });
  return clusters.map(adaptThermalClusterToView);
}

export async function getThermalCluster(
  studyId: StudyMetadata["id"],
  areaId: Area["name"],
  clusterId: Cluster["id"],
) {
  const cluster = await thermalApi.getThermalCluster({ studyId, areaId, clusterId });
  return adaptThermalClusterToView(cluster);
}

export async function updateThermalCluster(
  studyId: StudyMetadata["id"],
  areaId: Area["name"],
  clusterId: Cluster["id"],
  data: Partial<ThermalCluster>,
) {
  const cluster = await thermalApi.updateThermalCluster({
    studyId,
    areaId,
    clusterId,
    values: data,
  });
  return adaptThermalClusterToView(cluster);
}

export async function createThermalCluster(
  studyId: StudyMetadata["id"],
  areaId: Area["name"],
  data: PartialExceptFor<ThermalCluster, "name">,
) {
  const cluster = await thermalApi.createThermalCluster({ studyId, areaId, values: data });
  return adaptThermalClusterToView(cluster);
}

export async function duplicateThermalCluster(
  studyId: StudyMetadata["id"],
  areaId: Area["name"],
  sourceClusterId: ThermalCluster["id"],
  newName: ThermalCluster["name"],
) {
  const cluster = await thermalApi.duplicateThermalCluster({
    studyId,
    areaId,
    clusterId: sourceClusterId,
    newName,
  });
  return adaptThermalClusterToView(cluster);
}

export function deleteThermalClusters(
  studyId: StudyMetadata["id"],
  areaId: Area["name"],
  clusterIds: Array<Cluster["id"]>,
) {
  return thermalApi.deleteThermalClusters({ studyId, areaId, clusterIds });
}
