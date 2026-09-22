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
import type { ThermalCluster } from "@/services/api/studies/areas/thermals/types";
import type { Area, Cluster, StudyMetadata } from "@/types/types";
import type { PartialExceptFor } from "@/utils/tsUtils";

// TODO(PR2): remove compatibility exports and wrappers once consumers use the Thermal data layer.
export {
  COST_GENERATION_OPTIONS,
  THERMAL_GROUPS,
  THERMAL_POLLUTANTS,
  TS_GENERATION_OPTIONS,
  TS_LAW_OPTIONS,
} from "@/services/api/studies/areas/thermals/constants";
export type { ThermalCluster, ThermalGroup } from "@/services/api/studies/areas/thermals/types";

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

export type ThermalClusterWithCapacity = ClusterWithCapacity<ThermalCluster>;

export function getThermalClusters(studyId: StudyMetadata["id"], areaId: Area["name"]) {
  return thermalApi.getThermalClusters({ studyId, areaId });
}

export function getThermalCluster(
  studyId: StudyMetadata["id"],
  areaId: Area["name"],
  clusterId: Cluster["id"],
) {
  return thermalApi.getThermalCluster({ studyId, areaId, clusterId });
}

export function updateThermalCluster(
  studyId: StudyMetadata["id"],
  areaId: Area["name"],
  clusterId: Cluster["id"],
  data: Partial<ThermalCluster>,
) {
  return thermalApi.updateThermalCluster({ studyId, areaId, clusterId, values: data });
}

export function createThermalCluster(
  studyId: StudyMetadata["id"],
  areaId: Area["name"],
  data: PartialExceptFor<ThermalCluster, "name">,
) {
  return thermalApi.createThermalCluster({ studyId, areaId, values: data });
}

export function duplicateThermalCluster(
  studyId: StudyMetadata["id"],
  areaId: Area["name"],
  sourceClusterId: ThermalCluster["id"],
  newName: ThermalCluster["name"],
) {
  return thermalApi.duplicateThermalCluster({
    studyId,
    areaId,
    clusterId: sourceClusterId,
    newName,
  });
}

export function deleteThermalClusters(
  studyId: StudyMetadata["id"],
  areaId: Area["name"],
  clusterIds: Array<Cluster["id"]>,
) {
  return thermalApi.deleteThermalClusters({ studyId, areaId, clusterIds });
}
