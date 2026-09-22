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
import {
  createThermalClusterParamsSchema,
  thermalClusterSchema,
  thermalClustersSchema,
  updateThermalClusterParamsSchema,
} from "./schemas";
import type {
  CreateThermalClusterParams,
  DeleteThermalClustersParams,
  DuplicateThermalClusterParams,
  GetThermalClusterParams,
  ThermalCluster,
  ThermalsAreaParams,
  UpdateThermalClusterParams,
} from "./types";

/**
 * GET /v1/studies/{studyId}/areas/{areaId}/clusters/thermal - Lists complete thermal clusters.
 *
 * @param params - Study and area identifiers.
 * @returns All cluster properties, with IDs normalized for existing list consumers.
 * @throws If the response doesn't match the expected schema.
 */
export async function getThermalClusters(params: ThermalsAreaParams): Promise<ThermalCluster[]> {
  const { studyId, areaId } = params;
  const res = await client.get(`/v1/studies/${studyId}/areas/${areaId}/clusters/thermal`);
  const clusters = thermalClustersSchema.parse(res.data);
  // TODO: align ID normalization across all Thermal responses when migrating consumers.
  return clusters.map((cluster) => ({ ...cluster, id: nameToId(cluster.id) }));
}

/**
 * GET /v1/studies/{studyId}/areas/{areaId}/clusters/thermal/{clusterId} - Gets a thermal cluster.
 *
 * @param params - Study, area, and cluster identifiers.
 * @returns The complete cluster, preserving the server's ID casing.
 * @throws If the response doesn't match the expected schema.
 */
export async function getThermalCluster(params: GetThermalClusterParams): Promise<ThermalCluster> {
  const { studyId, areaId, clusterId } = params;
  const res = await client.get(
    `/v1/studies/${studyId}/areas/${areaId}/clusters/thermal/${clusterId}`,
  );
  return thermalClusterSchema.parse(res.data);
}

/**
 * POST /v1/studies/{studyId}/areas/{areaId}/clusters/thermal - Creates a thermal cluster.
 *
 * @param params - Study and area identifiers and the cluster values; only name is required.
 * @returns The created cluster, preserving the server's ID casing.
 * @throws If the values or response don't match the expected schema.
 */
export async function createThermalCluster(
  params: CreateThermalClusterParams,
): Promise<ThermalCluster> {
  const { studyId, areaId, values } = params;
  const body = createThermalClusterParamsSchema.parse(values);
  const res = await client.post(`/v1/studies/${studyId}/areas/${areaId}/clusters/thermal`, body);
  return thermalClusterSchema.parse(res.data);
}

/**
 * PATCH /v1/studies/{studyId}/areas/{areaId}/clusters/thermal/{clusterId} - Updates a thermal cluster.
 *
 * @param params - Identifiers and the partial cluster values to update.
 * @returns The updated cluster, preserving the server's ID casing.
 * @throws If the values or response don't match the expected schema.
 */
export async function updateThermalCluster(
  params: UpdateThermalClusterParams,
): Promise<ThermalCluster> {
  const { studyId, areaId, clusterId, values } = params;
  const body = updateThermalClusterParamsSchema.parse(values);
  const res = await client.patch(
    `/v1/studies/${studyId}/areas/${areaId}/clusters/thermal/${clusterId}`,
    body,
  );
  return thermalClusterSchema.parse(res.data);
}

/**
 * POST /v1/studies/{studyId}/areas/{areaId}/thermals/{clusterId} - Duplicates a thermal cluster.
 *
 * @param params - Source identifiers and the new name, sent as a query parameter.
 * @returns The duplicated cluster, preserving the server's ID casing.
 * @throws If the response doesn't match the expected schema.
 */
export async function duplicateThermalCluster(
  params: DuplicateThermalClusterParams,
): Promise<ThermalCluster> {
  const { studyId, areaId, clusterId, newName } = params;
  const res = await client.post(
    `/v1/studies/${studyId}/areas/${areaId}/thermals/${clusterId}`,
    null,
    { params: { newName } },
  );
  return thermalClusterSchema.parse(res.data);
}

/**
 * DELETE /v1/studies/{studyId}/areas/{areaId}/clusters/thermal - Deletes thermal clusters by ID.
 *
 * @param params - Study and area identifiers and the cluster IDs to send in the request body.
 */
export async function deleteThermalClusters(params: DeleteThermalClustersParams): Promise<void> {
  const { studyId, areaId, clusterIds } = params;
  await client.delete(`/v1/studies/${studyId}/areas/${areaId}/clusters/thermal`, {
    data: clusterIds,
  });
}
