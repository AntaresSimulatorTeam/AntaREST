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
  AdditionalConstraint,
  CreateAdditionalConstraintsParams,
  DeleteAdditionalConstraintsParams,
  GetAdditionalConstraintParams,
  GetAdditionalConstraintsParams,
  UpdateAdditionalConstraintsParams,
} from "./types";

const BASE_URL = "/v1/studies/{studyId}/areas/{areaId}/storages";
const URL = `${BASE_URL}/{storageId}/additional-constraints`;

////////////////////////////////////////////////////////////////
// Additional Constraints
////////////////////////////////////////////////////////////////

export async function getAdditionalConstraints({
  studyId,
  areaId,
  storageId,
}: GetAdditionalConstraintsParams) {
  const url = format(URL, { studyId, areaId, storageId });
  const { data } = await client.get<AdditionalConstraint[]>(url);
  return data;
}

export async function getAdditionalConstraint({
  studyId,
  areaId,
  storageId,
  constraintId,
}: GetAdditionalConstraintParams) {
  const url = format(`${URL}/{constraintId}`, {
    studyId,
    areaId,
    storageId,
    constraintId,
  });
  const { data } = await client.get<AdditionalConstraint>(url);
  return data;
}

export async function createAdditionalConstraints({
  studyId,
  areaId,
  storageId,
  constraints,
}: CreateAdditionalConstraintsParams) {
  const url = format(URL, { studyId, areaId, storageId });
  const { data } = await client.post<AdditionalConstraint[]>(url, constraints);
  return data;
}

export async function updateAdditionalConstraints({
  studyId,
  areaId,
  storageId,
  constraints,
}: UpdateAdditionalConstraintsParams) {
  const url = format(URL, { studyId, areaId, storageId });
  const { data } = await client.put<AdditionalConstraint[]>(url, constraints);
  return data;
}

export async function deleteAdditionalConstraints({
  studyId,
  areaId,
  constraintIds,
}: DeleteAdditionalConstraintsParams) {
  const url = format(`${BASE_URL}/additional-constraints`, { studyId, areaId });
  await client.delete(url, { data: constraintIds });
}
