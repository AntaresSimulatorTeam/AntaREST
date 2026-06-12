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
  createReserveParamsSchema,
  reserveGlobalParametersSchema,
  reserveSchema,
  reservesSchema,
  updateReserveGlobalParametersSchema,
  updateReserveParamsSchema,
} from "./schemas";
import type {
  CreateReserveParams,
  DeleteReservesParams,
  GetReserveParams,
  Reserve,
  ReserveGlobalParameters,
  ReservesAreaParams,
  UpdateReserveGlobalParametersParams,
  UpdateReserveParams,
} from "./types";

/**
 * GET /v1/studies/{studyId}/areas/{areaId}/reserves - Lists all reserves of an area.
 *
 * @param params - Study and area identifiers.
 * @returns The list of reserves for the given area.
 * @throws If the response doesn't match the expected schema.
 */
export async function getReserves(params: ReservesAreaParams): Promise<Reserve[]> {
  const { studyId, areaId } = params;
  const res = await client.get(`/v1/studies/${studyId}/areas/${areaId}/reserves`);
  return reservesSchema.parse(res.data);
}

/**
 * GET /v1/studies/{studyId}/areas/{areaId}/reserves/{reserveId} - Gets a reserve.
 *
 * @param params - Study, area, and reserve identifiers.
 * @returns The reserve data.
 * @throws If the response doesn't match the expected schema.
 */
export async function getReserve(params: GetReserveParams): Promise<Reserve> {
  const { studyId, areaId, reserveId } = params;
  const res = await client.get(`/v1/studies/${studyId}/areas/${areaId}/reserves/${reserveId}`);
  return reserveSchema.parse(res.data);
}

/**
 * POST /v1/studies/{studyId}/areas/{areaId}/reserves - Creates a new reserve.
 *
 * @param params - Study, area identifiers and the reserve data to create.
 * @returns The created reserve data.
 * @throws If the params or response doesn't match the expected schema.
 */
export async function createReserve(params: CreateReserveParams): Promise<Reserve> {
  const { studyId, areaId, data } = params;
  const body = createReserveParamsSchema.parse(data);
  const res = await client.post(`/v1/studies/${studyId}/areas/${areaId}/reserves`, body);
  return reserveSchema.parse(res.data);
}

/**
 * PATCH /v1/studies/{studyId}/areas/{areaId}/reserves/{reserveId} - Updates a reserve.
 *
 * @param params - Identifiers and the partial reserve data to update.
 * @returns The updated reserve data.
 * @throws If the params or response doesn't match the expected schema.
 */
export async function updateReserve(params: UpdateReserveParams): Promise<Reserve> {
  const { studyId, areaId, reserveId, data } = params;
  const body = updateReserveParamsSchema.parse(data);
  const res = await client.patch(
    `/v1/studies/${studyId}/areas/${areaId}/reserves/${reserveId}`,
    body,
  );
  return reserveSchema.parse(res.data);
}

/**
 * DELETE /v1/studies/{studyId}/areas/{areaId}/reserves - Deletes reserves by ID.
 *
 * @param params - Identifiers and the list of reserve IDs to delete.
 */
export async function deleteReserves(params: DeleteReservesParams) {
  const { studyId, areaId, reserveIds } = params;
  await client.delete(`/v1/studies/${studyId}/areas/${areaId}/reserves`, {
    data: reserveIds,
  });
}

/**
 * GET /v1/studies/{studyId}/areas/{areaId}/reserves/global-parameters - Gets the global
 * reserve parameters for an area.
 *
 * @param params - Study and area identifiers.
 * @returns The global reserve parameters.
 * @throws If the response doesn't match the expected schema.
 */
export async function getReserveGlobalParameters(
  params: ReservesAreaParams,
): Promise<ReserveGlobalParameters> {
  const { studyId, areaId } = params;
  const res = await client.get(`/v1/studies/${studyId}/areas/${areaId}/reserves/global-parameters`);
  return reserveGlobalParametersSchema.parse(res.data);
}

/**
 * PUT /v1/studies/{studyId}/areas/{areaId}/reserves/global-parameters - Updates the global
 * reserve parameters for an area.
 *
 * @param params - Identifiers and the partial global parameters to update.
 * @returns The updated global reserve parameters.
 * @throws If the params or response doesn't match the expected schema.
 */
export async function updateReserveGlobalParameters(
  params: UpdateReserveGlobalParametersParams,
): Promise<ReserveGlobalParameters> {
  const { studyId, areaId, data } = params;
  const body = updateReserveGlobalParametersSchema.parse(data);
  const res = await client.put(
    `/v1/studies/${studyId}/areas/${areaId}/reserves/global-parameters`,
    body,
  );
  return reserveGlobalParametersSchema.parse(res.data);
}
