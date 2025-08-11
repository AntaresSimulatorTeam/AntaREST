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
  BaseStorageParams,
  CreateAdditionalConstraintsParams,
  DeleteAdditionalConstraintsParams,
  GetAdditionalConstraintParams,
  UpdateAdditionalConstraintsParams,
} from "./types";

const BASE_URL = "/v1/studies/{studyId}/areas/{areaId}/storages";
const CONSTRAINTS_URL = `${BASE_URL}/{storageId}/additional-constraints`;

const buildUrl = (params: BaseStorageParams & { constraintId?: string }) =>
  format(params.constraintId ? `${CONSTRAINTS_URL}/{constraintId}` : CONSTRAINTS_URL, params);

export async function getAdditionalConstraints(params: BaseStorageParams) {
  const { data } = await client.get<AdditionalConstraint[]>(buildUrl(params));
  return data;
}

export async function getAdditionalConstraint(params: GetAdditionalConstraintParams) {
  const { data } = await client.get<AdditionalConstraint>(buildUrl(params));
  return data;
}

export async function createAdditionalConstraints<T>({
  constraints,
  ...params
}: CreateAdditionalConstraintsParams<T>) {
  const { data } = await client.post<AdditionalConstraint[]>(buildUrl(params), constraints);
  return data;
}

export async function updateAdditionalConstraints<T>({
  constraints,
  ...params
}: UpdateAdditionalConstraintsParams<T>) {
  const { data } = await client.put<AdditionalConstraint[]>(buildUrl(params), constraints);
  return data;
}

export async function deleteAdditionalConstraints({
  constraintIds,
  ...params
}: DeleteAdditionalConstraintsParams) {
  await client.delete(buildUrl(params), { data: constraintIds });
}
