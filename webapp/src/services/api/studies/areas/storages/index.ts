/**
 * Copyright (c) 2025, RTE (https://www.rte-france.com)
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
import type {
  CreateStorageAdditionalConstraintsParams,
  DeleteStorageAdditionalConstraintsParams,
  GetStorageAdditionalConstraintParams,
  GetStorageAdditionalConstraintsParams,
  StorageAdditionalConstraint,
  UpdateStorageAdditionalConstraintsParams,
} from "./types";

const BASE_URL = "/v1/studies/{studyId}/areas/{areaId}/storages";
const URL = `${BASE_URL}/{storageId}/additional-constraints`;

////////////////////////////////////////////////////////////////
// Additional Constraints
////////////////////////////////////////////////////////////////

export async function getStorageAdditionalConstraints({
  studyId,
  areaId,
  storageId,
}: GetStorageAdditionalConstraintsParams) {
  const url = format(URL, { studyId, areaId, storageId });
  const { data } = await client.get<StorageAdditionalConstraint[]>(url);
  return data;
}

export async function getStorageAdditionalConstraint({
  studyId,
  areaId,
  storageId,
  constraintId,
}: GetStorageAdditionalConstraintParams) {
  const url = format(`${URL}/{constraintId}`, {
    studyId,
    areaId,
    storageId,
    constraintId,
  });
  const { data } = await client.get<StorageAdditionalConstraint>(url);
  return data;
}

export async function createStorageAdditionalConstraints({
  studyId,
  areaId,
  storageId,
  constraints,
}: CreateStorageAdditionalConstraintsParams) {
  const url = format(URL, { studyId, areaId, storageId });
  const { data } = await client.post<StorageAdditionalConstraint[]>(url, constraints);
  return data;
}

export async function updateStorageAdditionalConstraints({
  studyId,
  areaId,
  storageId,
  constraints,
}: UpdateStorageAdditionalConstraintsParams) {
  const url = format(URL, { studyId, areaId, storageId });
  const { data } = await client.put<StorageAdditionalConstraint[]>(url, constraints);
  return data;
}

export async function deleteStorageAdditionalConstraints({
  studyId,
  areaId,
  constraintIds,
}: DeleteStorageAdditionalConstraintsParams) {
  const url = format(`${BASE_URL}/additional-constraints`, { studyId, areaId });
  await client.delete(url, { data: constraintIds });
}
