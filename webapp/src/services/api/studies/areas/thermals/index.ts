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
import {
  thermalCreationSchema,
  thermalSchema,
  thermalsSchema,
  thermalUpdateSchema,
} from "./schemas";
import type {
  CreateThermalParams,
  DeleteThermalsParams,
  DuplicateThermalParams,
  Thermal,
  ThermalParams,
  ThermalsParams,
  UpdateThermalParams,
} from "./types";

/**
 * GET /v1/studies/{studyId}/areas/{areaId}/clusters/thermal - Lists complete thermal clusters.
 *
 * @param params - Study and area identifiers.
 * @param params.studyId - Study identifier.
 * @param params.areaId - Area identifier.
 * @returns All cluster properties, with IDs normalized for existing list consumers.
 * @throws If the response doesn't match the expected schema.
 */
export async function getThermals({ studyId, areaId }: ThermalsParams): Promise<Thermal[]> {
  const res = await client.get(`/v1/studies/${studyId}/areas/${areaId}/clusters/thermal`);
  return thermalsSchema.parse(res.data);
}

/**
 * GET /v1/studies/{studyId}/areas/{areaId}/clusters/thermal/{thermalId} - Gets a thermal cluster.
 *
 * @param params - Study, area, and thermal cluster identifiers.
 * @param params.studyId - Study identifier.
 * @param params.areaId - Area identifier.
 * @param params.thermalId - Thermal cluster identifier.
 * @returns The complete cluster, with a normalized ID.
 * @throws If the response doesn't match the expected schema.
 */
export async function getThermal({ studyId, areaId, thermalId }: ThermalParams): Promise<Thermal> {
  const res = await client.get(
    `/v1/studies/${studyId}/areas/${areaId}/clusters/thermal/${thermalId}`,
  );
  return thermalSchema.parse(res.data);
}

/**
 * POST /v1/studies/{studyId}/areas/{areaId}/clusters/thermal - Creates a thermal cluster.
 *
 * @param params - Study and area identifiers and the cluster values; only name is required.
 * @param params.studyId - Study identifier.
 * @param params.areaId - Area identifier.
 * @param params.values - Cluster values; only name is required.
 * @returns The created cluster, with a normalized ID.
 * @throws If the values or response don't match the expected schema.
 */
export async function createThermal({
  studyId,
  areaId,
  values,
}: CreateThermalParams): Promise<Thermal> {
  const body = thermalCreationSchema.parse(values);
  const res = await client.post(`/v1/studies/${studyId}/areas/${areaId}/clusters/thermal`, body);
  return thermalSchema.parse(res.data);
}

/**
 * PATCH /v1/studies/{studyId}/areas/{areaId}/clusters/thermal/{thermalId} - Updates a thermal cluster.
 *
 * @param params - Identifiers and the partial cluster values to update.
 * @param params.studyId - Study identifier.
 * @param params.areaId - Area identifier.
 * @param params.thermalId - Thermal cluster identifier.
 * @param params.values - Partial cluster values to update.
 * @returns The updated cluster, with a normalized ID.
 * @throws If the values or response don't match the expected schema.
 */
export async function updateThermal({
  studyId,
  areaId,
  thermalId,
  values,
}: UpdateThermalParams): Promise<Thermal> {
  const body = thermalUpdateSchema.parse(values);
  const res = await client.patch(
    `/v1/studies/${studyId}/areas/${areaId}/clusters/thermal/${thermalId}`,
    body,
  );
  return thermalSchema.parse(res.data);
}

/**
 * POST /v1/studies/{studyId}/areas/{areaId}/thermals/{thermalId} - Duplicates a thermal cluster.
 *
 * @param params - Source identifiers and the new name, sent as a query parameter.
 * @param params.studyId - Study identifier.
 * @param params.areaId - Area identifier.
 * @param params.thermalId - Source thermal cluster identifier.
 * @param params.newName - New cluster name.
 * @returns The duplicated cluster, with a normalized ID.
 * @throws If the response doesn't match the expected schema.
 */
export async function duplicateThermal({
  studyId,
  areaId,
  thermalId,
  newName,
}: DuplicateThermalParams): Promise<Thermal> {
  const res = await client.post(
    `/v1/studies/${studyId}/areas/${areaId}/thermals/${thermalId}`,
    null,
    { params: { newName } },
  );
  return thermalSchema.parse(res.data);
}

/**
 * DELETE /v1/studies/{studyId}/areas/{areaId}/clusters/thermal - Deletes thermal clusters by ID.
 *
 * @param params - Study and area identifiers and the cluster IDs to send in the request body.
 * @param params.studyId - Study identifier.
 * @param params.areaId - Area identifier.
 * @param params.thermalIds - Thermal cluster identifiers to delete.
 */
export async function deleteThermals({
  studyId,
  areaId,
  thermalIds,
}: DeleteThermalsParams): Promise<void> {
  await client.delete(`/v1/studies/${studyId}/areas/${areaId}/clusters/thermal`, {
    data: thermalIds,
  });
}
