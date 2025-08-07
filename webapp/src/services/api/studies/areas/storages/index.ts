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
const CONSTRAINTS_URL = `${BASE_URL}/{storageId}/additional-constraints`;

const buildConstraintUrl = (
  params: { studyId: string; areaId: string; storageId: string },
  constraintId?: string,
) => {
  const url = format(CONSTRAINTS_URL, params);
  return constraintId ? `${url}/${constraintId}` : url;
};

export async function getAdditionalConstraints(params: GetAdditionalConstraintsParams) {
  const { data } = await client.get<AdditionalConstraint[]>(buildConstraintUrl(params));
  return data;
}

export async function getAdditionalConstraint({
  constraintId,
  ...params
}: GetAdditionalConstraintParams) {
  const { data } = await client.get<AdditionalConstraint>(buildConstraintUrl(params, constraintId));
  return data;
}

export async function createAdditionalConstraints({
  constraints,
  ...params
}: CreateAdditionalConstraintsParams) {
  const { data } = await client.post<AdditionalConstraint[]>(
    buildConstraintUrl(params),
    constraints,
  );
  return data;
}

export async function updateAdditionalConstraints({
  constraints,
  ...params
}: UpdateAdditionalConstraintsParams) {
  const { data } = await client.put<AdditionalConstraint[]>(
    buildConstraintUrl(params),
    constraints,
  );
  return data;
}

export async function deleteAdditionalConstraints({
  constraintIds,
  ...params
}: DeleteAdditionalConstraintsParams) {
  await client.delete(buildConstraintUrl(params), { data: constraintIds });
}
