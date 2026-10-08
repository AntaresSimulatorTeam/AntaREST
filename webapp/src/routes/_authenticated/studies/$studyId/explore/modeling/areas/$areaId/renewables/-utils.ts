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

import * as renewableApi from "@/services/api/studies/areas/renewables";
import type { Area, Cluster, StudyMetadata } from "@/types/types";
import type { PartialExceptFor } from "@/utils/tsUtils";
import type { ClusterWithCapacity } from "../-clustersUtils";
import { adaptRenewableClusterToView } from "./-adapters";

// TODO(PR2): remove compatibility exports and wrappers once consumers use the Renewable data layer.
export {
  RENEWABLE_GROUPS,
  TS_INTERPRETATION_OPTIONS,
} from "@/services/api/studies/areas/renewables/constants";
export type { RenewableGroup } from "@/services/api/studies/areas/renewables/types";

export type RenewableCluster = ReturnType<typeof adaptRenewableClusterToView>;
export type RenewableClusterWithCapacity = ClusterWithCapacity<RenewableCluster>;

export async function getRenewableClusters(studyId: StudyMetadata["id"], areaId: Area["name"]) {
  const clusters = await renewableApi.getRenewableClusters({ studyId, areaId });
  return clusters.map(adaptRenewableClusterToView);
}

export async function getRenewableCluster(
  studyId: StudyMetadata["id"],
  areaId: Area["name"],
  clusterId: Cluster["id"],
) {
  const cluster = await renewableApi.getRenewableCluster({ studyId, areaId, clusterId });
  return adaptRenewableClusterToView(cluster);
}

export async function updateRenewableCluster(
  studyId: StudyMetadata["id"],
  areaId: Area["name"],
  clusterId: Cluster["id"],
  data: Partial<RenewableCluster>,
) {
  const cluster = await renewableApi.updateRenewableCluster({
    studyId,
    areaId,
    clusterId,
    values: data,
  });
  return adaptRenewableClusterToView(cluster);
}

export async function createRenewableCluster(
  studyId: StudyMetadata["id"],
  areaId: Area["name"],
  data: PartialExceptFor<RenewableCluster, "name">,
) {
  const cluster = await renewableApi.createRenewableCluster({ studyId, areaId, values: data });
  return adaptRenewableClusterToView(cluster);
}

export async function duplicateRenewableCluster(
  studyId: StudyMetadata["id"],
  areaId: Area["name"],
  sourceClusterId: RenewableCluster["id"],
  newName: RenewableCluster["name"],
) {
  const cluster = await renewableApi.duplicateRenewableCluster({
    studyId,
    areaId,
    clusterId: sourceClusterId,
    newName,
  });
  return adaptRenewableClusterToView(cluster);
}

export function deleteRenewableClusters(
  studyId: StudyMetadata["id"],
  areaId: Area["name"],
  clusterIds: Array<Cluster["id"]>,
) {
  return renewableApi.deleteRenewableClusters({ studyId, areaId, clusterIds });
}
