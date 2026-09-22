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

import client from "@/services/api/client";
import { nameToId } from "@/services/utils";
import { format } from "@/utils/stringUtils";
import type {
  CreateThermalClusterParams,
  DeleteThermalClustersParams,
  DuplicateThermalClusterParams,
  GetThermalClusterParams,
  ThermalCluster,
  ThermalsAreaParams,
  UpdateThermalClusterParams,
} from "./types";

const CLUSTERS_URL = "/v1/studies/{studyId}/areas/{areaId}/clusters/thermal";
const CLUSTER_URL = `${CLUSTERS_URL}/{clusterId}`;
const DUPLICATE_URL = "/v1/studies/{studyId}/areas/{areaId}/thermals/{clusterId}";

export async function getThermalClusters(params: ThermalsAreaParams) {
  const { data } = await client.get<ThermalCluster[]>(format(CLUSTERS_URL, params));
  // TODO(PR2): align ID normalization across all Thermal responses when migrating consumers.
  return data.map((cluster) => ({ ...cluster, id: nameToId(cluster.id) }));
}

export async function getThermalCluster(params: GetThermalClusterParams) {
  const { data } = await client.get<ThermalCluster>(format(CLUSTER_URL, params));
  return data;
}

export async function createThermalCluster({ values, ...params }: CreateThermalClusterParams) {
  const { data } = await client.post<ThermalCluster>(format(CLUSTERS_URL, params), values);
  return data;
}

export async function updateThermalCluster({ values, ...params }: UpdateThermalClusterParams) {
  const { data } = await client.patch<ThermalCluster>(format(CLUSTER_URL, params), values);
  return data;
}

export async function duplicateThermalCluster({
  newName,
  ...params
}: DuplicateThermalClusterParams) {
  const { data } = await client.post<ThermalCluster>(format(DUPLICATE_URL, params), null, {
    params: { newName },
  });
  return data;
}

export async function deleteThermalClusters({
  clusterIds,
  ...params
}: DeleteThermalClustersParams) {
  await client.delete(format(CLUSTERS_URL, params), { data: clusterIds });
}
