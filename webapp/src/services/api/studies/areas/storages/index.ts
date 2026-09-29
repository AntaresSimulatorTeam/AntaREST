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
import { format } from "@/utils/stringUtils";
import * as R from "ramda";
import {
  storageCreationSchema,
  storageSchema,
  storagesSchema,
  storageUpdateSchema,
} from "./schemas";
import type {
  CreateStorageConstraintParams,
  CreateStorageConstraintsParams,
  CreateStorageParams,
  DeleteStorageConstraintParams,
  DeleteStorageConstraintsParams,
  DeleteStoragesParams,
  DuplicateStorageParams,
  GetStorageConstraintParams,
  Storage,
  StorageConstraint,
  StorageParams,
  StoragesAreaParams,
  UpdateStorageConstraintParams,
  UpdateStorageConstraintsParams,
  UpdateStorageParams,
} from "./types";

/**
 * GET /v1/studies/{studyId}/areas/{areaId}/storages - Lists complete short-term storages.
 *
 * @param params - Request identifiers and values.
 * @param params.studyId - Study identifier.
 * @param params.areaId - Area identifier.
 * @returns All storage properties, preserving server IDs.
 * @throws If the response doesn't match the expected schema.
 */
export async function getStorages({ studyId, areaId }: StoragesAreaParams): Promise<Storage[]> {
  const { data } = await client.get(`/v1/studies/${studyId}/areas/${areaId}/storages`);
  return storagesSchema.parse(data);
}

/**
 * GET /v1/studies/{studyId}/areas/{areaId}/storages/{storageId} - Gets a short-term storage.
 *
 * @param params - Request identifiers and values.
 * @param params.studyId - Study identifier.
 * @param params.areaId - Area identifier.
 * @param params.storageId - Storage identifier.
 * @returns The complete storage, preserving its server ID.
 * @throws If the response doesn't match the expected schema.
 */
export async function getStorage({ studyId, areaId, storageId }: StorageParams): Promise<Storage> {
  const { data } = await client.get(`/v1/studies/${studyId}/areas/${areaId}/storages/${storageId}`);
  return storageSchema.parse(data);
}

/**
 * POST /v1/studies/{studyId}/areas/{areaId}/storages - Creates a short-term storage.
 *
 * @param params - Request identifiers and values.
 * @param params.studyId - Study identifier.
 * @param params.areaId - Area identifier.
 * @param params.values - Storage values; only name is required.
 * @returns The created storage.
 * @throws If the values or response don't match the expected schema.
 */
export async function createStorage({
  studyId,
  areaId,
  values,
}: CreateStorageParams): Promise<Storage> {
  const body = storageCreationSchema.parse(values);
  const { data } = await client.post(`/v1/studies/${studyId}/areas/${areaId}/storages`, body);
  return storageSchema.parse(data);
}

/**
 * PATCH /v1/studies/{studyId}/areas/{areaId}/storages/{storageId} - Updates a short-term storage.
 *
 * @param params - Request identifiers and values.
 * @param params.studyId - Study identifier.
 * @param params.areaId - Area identifier.
 * @param params.storageId - Storage identifier.
 * @param params.values - Partial storage values to update.
 * @returns The updated storage.
 * @throws If the values or response don't match the expected schema.
 */
export async function updateStorage({
  studyId,
  areaId,
  storageId,
  values,
}: UpdateStorageParams): Promise<Storage> {
  const body = storageUpdateSchema.parse(values);
  const { data } = await client.patch(
    `/v1/studies/${studyId}/areas/${areaId}/storages/${storageId}`,
    body,
  );
  return storageSchema.parse(data);
}

/**
 * POST /v1/studies/{studyId}/areas/{areaId}/storages/{storageId} - Duplicates a short-term storage.
 *
 * @param params - Request identifiers and values.
 * @param params.studyId - Study identifier.
 * @param params.areaId - Area identifier.
 * @param params.storageId - Source storage identifier.
 * @param params.newName - New storage name, sent as a query parameter.
 * @returns The duplicated storage.
 * @throws If the response doesn't match the expected schema.
 */
export async function duplicateStorage({
  studyId,
  areaId,
  storageId,
  newName,
}: DuplicateStorageParams): Promise<Storage> {
  const { data } = await client.post(
    `/v1/studies/${studyId}/areas/${areaId}/storages/${storageId}`,
    null,
    { params: { newName } },
  );
  return storageSchema.parse(data);
}

/**
 * DELETE /v1/studies/{studyId}/areas/{areaId}/storages - Deletes short-term storages by ID.
 *
 * @param params - Request identifiers and values.
 * @param params.studyId - Study identifier.
 * @param params.areaId - Area identifier.
 * @param params.storageIds - Storage identifiers to send in the request body.
 */
export async function deleteStorages({
  studyId,
  areaId,
  storageIds,
}: DeleteStoragesParams): Promise<void> {
  await client.delete(`/v1/studies/${studyId}/areas/${areaId}/storages`, { data: storageIds });
}

////////////////////////////////////////////////////////////////
// Additional Constraints
////////////////////////////////////////////////////////////////

const BASE_URL = "/v1/studies/{studyId}/areas/{areaId}/storages";
const CONSTRAINTS_URL = `${BASE_URL}/{storageId}/additional-constraints`;
const CONSTRAINT_URL = `${CONSTRAINTS_URL}/{constraintId}`;

export async function getStorageConstraints(params: StorageParams) {
  const url = format(CONSTRAINTS_URL, params);
  const { data } = await client.get<StorageConstraint[]>(url);
  return data;
}

export async function getStorageConstraint(params: GetStorageConstraintParams) {
  const url = format(CONSTRAINT_URL, params);
  const { data } = await client.get<StorageConstraint>(url);
  return data;
}

export async function createStorageConstraints({
  constraints,
  ...params
}: CreateStorageConstraintsParams) {
  const url = format(CONSTRAINTS_URL, params);
  const validConstraints = constraints.map(
    R.pick(["name", "variable", "operator", "occurrences", "enabled"]),
  );

  const { data } = await client.post<StorageConstraint[]>(url, validConstraints);

  return data;
}

export async function createStorageConstraint({
  values,
  ...params
}: CreateStorageConstraintParams) {
  const createdConstraints = await createStorageConstraints({
    ...params,
    constraints: [values],
  });

  return createdConstraints[0];
}

export async function updateStorageConstraints({
  constraints,
  ...params
}: UpdateStorageConstraintsParams) {
  const url = format(CONSTRAINTS_URL, params);
  const validConstraints = R.map(
    R.pick(["variable", "operator", "occurrences", "enabled"]),
    constraints,
  );

  const { data } = await client.put<StorageConstraint[]>(url, validConstraints);

  return data;
}

export async function updateStorageConstraint({
  constraintId,
  values,
  ...params
}: UpdateStorageConstraintParams) {
  const updatedConstraints = await updateStorageConstraints({
    ...params,
    constraints: { [constraintId]: values },
  });

  return updatedConstraints[0];
}

export async function deleteStorageConstraints({
  constraintIds,
  ...params
}: DeleteStorageConstraintsParams) {
  const url = format(CONSTRAINTS_URL, params);
  await client.delete(url, { data: constraintIds });
}

export async function deleteStorageConstraint({
  constraintId,
  ...params
}: DeleteStorageConstraintParams) {
  await deleteStorageConstraints({ ...params, constraintIds: [constraintId] });
}
