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
import * as R from "ramda";
import type {
  CreateStorageConstraintParams,
  CreateStorageConstraintsParams,
  DeleteStorageConstraintParams,
  DeleteStorageConstraintsParams,
  GetStorageConstraintParams,
  StorageConstraint,
  StorageParams,
  UpdateStorageConstraintParams,
  UpdateStorageConstraintsParams,
} from "./types";

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
  //! ⚠️ DON'T FORGET TO REMOVE THIS LINE ⚠️
  await new Promise((res) => setTimeout(() => res(1), 5000));

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
  //! ⚠️ DON'T FORGET TO REMOVE THIS LINE ⚠️
  await new Promise((res) => setTimeout(() => res(1), 2000));

  await deleteStorageConstraints({ ...params, constraintIds: [constraintId] });
}
