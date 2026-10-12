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
  renewableCreationSchema,
  renewableSchema,
  renewablesSchema,
  renewableUpdateSchema,
} from "./schemas";
import type {
  CreateRenewableParams,
  DeleteRenewablesParams,
  DuplicateRenewableParams,
  GetRenewableParams,
  Renewable,
  RenewablesAreaParams,
  UpdateRenewableParams,
} from "./types";

/**
 * GET /v1/studies/{studyId}/areas/{areaId}/clusters/renewable - Lists complete renewable clusters.
 *
 * @param params - Study and area identifiers.
 * @param params.studyId - Study identifier.
 * @param params.areaId - Area identifier.
 * @returns All cluster properties, with IDs normalized for existing list consumers.
 * @throws If the response doesn't match the expected schema.
 */
export async function getRenewables({
  studyId,
  areaId,
}: RenewablesAreaParams): Promise<Renewable[]> {
  const res = await client.get(`/v1/studies/${studyId}/areas/${areaId}/clusters/renewable`);
  const clusters = renewablesSchema.parse(res.data);
  // The backend model preserves name casing for backward compatibility,
  // while database storage lowercases IDs. Creation and file-backed reads can therefore
  // return different ID casing from database-backed reads.
  // TODO: Return canonical lowercase IDs consistently from the API, then remove this normalization.
  return clusters.map((cluster) => ({ ...cluster, id: nameToId(cluster.id) }));
}

/**
 * GET /v1/studies/{studyId}/areas/{areaId}/clusters/renewable/{renewableId} - Gets a renewable cluster.
 *
 * @param params - Study, area, and cluster identifiers.
 * @param params.studyId - Study identifier.
 * @param params.areaId - Area identifier.
 * @param params.renewableId - Cluster identifier.
 * @returns The complete cluster, with a normalized ID.
 * @throws If the response doesn't match the expected schema.
 */
export async function getRenewable({
  studyId,
  areaId,
  renewableId,
}: GetRenewableParams): Promise<Renewable> {
  const res = await client.get(
    `/v1/studies/${studyId}/areas/${areaId}/clusters/renewable/${renewableId}`,
  );
  const cluster = renewableSchema.parse(res.data);
  // TODO: Return canonical lowercase IDs consistently from the API, then remove this normalization.
  return { ...cluster, id: nameToId(cluster.id) };
}

/**
 * POST /v1/studies/{studyId}/areas/{areaId}/clusters/renewable - Creates a renewable cluster.
 *
 * @param params - Study and area identifiers and the cluster values; only name is required.
 * @param params.studyId - Study identifier.
 * @param params.areaId - Area identifier.
 * @param params.values - Cluster values; only name is required.
 * @returns The created cluster, preserving the server's ID casing.
 * @throws If the values or response don't match the expected schema.
 */
export async function createRenewable({
  studyId,
  areaId,
  values,
}: CreateRenewableParams): Promise<Renewable> {
  const body = renewableCreationSchema.parse(values);
  const res = await client.post(`/v1/studies/${studyId}/areas/${areaId}/clusters/renewable`, body);
  return renewableSchema.parse(res.data);
}

/**
 * PATCH /v1/studies/{studyId}/areas/{areaId}/clusters/renewable/{renewableId} - Updates a renewable cluster.
 *
 * @param params - Identifiers and the partial cluster values to update.
 * @param params.studyId - Study identifier.
 * @param params.areaId - Area identifier.
 * @param params.renewableId - Cluster identifier.
 * @param params.values - Partial cluster values to update.
 * @returns The updated cluster, preserving the server's ID casing.
 * @throws If the values or response don't match the expected schema.
 */
export async function updateRenewable({
  studyId,
  areaId,
  renewableId,
  values,
}: UpdateRenewableParams): Promise<Renewable> {
  const body = renewableUpdateSchema.parse(values);
  const res = await client.patch(
    `/v1/studies/${studyId}/areas/${areaId}/clusters/renewable/${renewableId}`,
    body,
  );
  return renewableSchema.parse(res.data);
}

/**
 * POST /v1/studies/{studyId}/areas/{areaId}/renewables/{renewableId} - Duplicates a renewable cluster.
 *
 * @param params - Source identifiers and the new name, sent as a query parameter.
 * @param params.studyId - Study identifier.
 * @param params.areaId - Area identifier.
 * @param params.renewableId - Source cluster identifier.
 * @param params.newName - New cluster name.
 * @returns The duplicated cluster, preserving the server's ID casing.
 * @throws If the response doesn't match the expected schema.
 */
export async function duplicateRenewable({
  studyId,
  areaId,
  renewableId,
  newName,
}: DuplicateRenewableParams): Promise<Renewable> {
  const res = await client.post(
    `/v1/studies/${studyId}/areas/${areaId}/renewables/${renewableId}`,
    null,
    { params: { newName } },
  );
  return renewableSchema.parse(res.data);
}

/**
 * DELETE /v1/studies/{studyId}/areas/{areaId}/clusters/renewable - Deletes renewable clusters by ID.
 *
 * @param params - Study and area identifiers and the cluster IDs to send in the request body.
 * @param params.studyId - Study identifier.
 * @param params.areaId - Area identifier.
 * @param params.renewableIds - Renewable cluster identifiers to delete.
 */
export async function deleteRenewables({
  studyId,
  areaId,
  renewableIds,
}: DeleteRenewablesParams): Promise<void> {
  await client.delete(`/v1/studies/${studyId}/areas/${areaId}/clusters/renewable`, {
    data: renewableIds,
  });
}
