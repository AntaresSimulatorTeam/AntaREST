/** Copyright (c) 2024, RTE (https://www.rte-france.com)
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
  Area,
  Cluster,
  StudyMetadata,
} from "../../../../../../../common/types";
import client from "../../../../../../../services/api/client";
import type { PartialExceptFor } from "../../../../../../../utils/tsUtils";
import type { ClusterWithCapacity } from "../common/clustersUtils";

////////////////////////////////////////////////////////////////
// Constants
////////////////////////////////////////////////////////////////

export const RENEWABLE_GROUPS = [
  "Wind Onshore",
  "Wind Offshore",
  "Solar Thermal",
  "Solar PV",
  "Solar Rooftop",
  "Other RES 1",
  "Other RES 2",
  "Other RES 3",
  "Other RES 4",
] as const;

export const TS_INTERPRETATION_OPTIONS = [
  "power-generation",
  "production-factor",
] as const;

////////////////////////////////////////////////////////////////
// Types
////////////////////////////////////////////////////////////////

export type RenewableGroup = (typeof RENEWABLE_GROUPS)[number];

type TimeSeriesInterpretation = (typeof TS_INTERPRETATION_OPTIONS)[number];

export interface RenewableFormFields {
  name: string;
  group: string;
  tsInterpretation: TimeSeriesInterpretation;
  enabled: boolean;
  unitCount: number;
  nominalCapacity: number;
}

export interface RenewableCluster {
  id: string;
  name: string;
  group: RenewableGroup;
  tsInterpretation: TimeSeriesInterpretation;
  enabled: boolean;
  unitCount: number;
  nominalCapacity: number;
}

export type RenewableClusterWithCapacity =
  ClusterWithCapacity<RenewableCluster>;

////////////////////////////////////////////////////////////////
// Functions
////////////////////////////////////////////////////////////////

const getClustersUrl = (
  studyId: StudyMetadata["id"],
  areaId: Area["name"],
): string => `/v1/studies/${studyId}/areas/${areaId}/clusters/renewable`;

const getClusterUrl = (
  studyId: StudyMetadata["id"],
  areaId: Area["name"],
  clusterId: Cluster["id"],
): string => `${getClustersUrl(studyId, areaId)}/${clusterId}`;

////////////////////////////////////////////////////////////////
// API
////////////////////////////////////////////////////////////////

export async function getRenewableClusters(
  studyId: StudyMetadata["id"],
  areaId: Area["name"],
) {
  const res = await client.get<RenewableCluster[]>(
    getClustersUrl(studyId, areaId),
  );
  return res.data;
}

export async function getRenewableCluster(
  studyId: StudyMetadata["id"],
  areaId: Area["name"],
  clusterId: Cluster["id"],
) {
  const res = await client.get<RenewableCluster>(
    getClusterUrl(studyId, areaId, clusterId),
  );
  return res.data;
}

export async function updateRenewableCluster(
  studyId: StudyMetadata["id"],
  areaId: Area["name"],
  clusterId: Cluster["id"],
  data: Partial<RenewableCluster>,
) {
  const res = await client.patch<RenewableCluster>(
    getClusterUrl(studyId, areaId, clusterId),
    data,
  );
  return res.data;
}

export async function createRenewableCluster(
  studyId: StudyMetadata["id"],
  areaId: Area["name"],
  data: PartialExceptFor<RenewableCluster, "name">,
) {
  const res = await client.post<RenewableCluster>(
    getClustersUrl(studyId, areaId),
    data,
  );
  return res.data;
}

export async function duplicateRenewableCluster(
  studyId: StudyMetadata["id"],
  areaId: Area["name"],
  sourceClusterId: RenewableCluster["id"],
  newName: RenewableCluster["name"],
) {
  const res = await client.post<RenewableCluster>(
    `/v1/studies/${studyId}/areas/${areaId}/renewables/${sourceClusterId}`,
    null,
    { params: { newName } },
  );
  return res.data;
}

export async function deleteRenewableClusters(
  studyId: StudyMetadata["id"],
  areaId: Area["name"],
  clusterIds: Array<Cluster["id"]>,
) {
  await client.delete(getClustersUrl(studyId, areaId), { data: clusterIds });
}
