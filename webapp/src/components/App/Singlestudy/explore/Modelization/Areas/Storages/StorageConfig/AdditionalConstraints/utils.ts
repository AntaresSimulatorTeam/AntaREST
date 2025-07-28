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
import type { Area, StudyMetadata } from "@/types/types";
import type { Storage } from "../../utils";

////////////////////////////////////////////////////////////////
// Types
////////////////////////////////////////////////////////////////

export type ConstraintVariable = "withdrawal" | "injection" | "netting";

export type ConstraintOperator = "less" | "greater" | "equal";

export interface AdditionalConstraint {
  id: string;
  variable: ConstraintVariable;
  operator: ConstraintOperator;
  enabled: boolean;
  hours: number[][];
}

export interface CreateAdditionalConstraintParams {
  name: string;
  variable: ConstraintVariable;
  bounds: ConstraintOperator;
  enabled?: boolean;
  hours: number[][];
}

////////////////////////////////////////////////////////////////
// URLs
////////////////////////////////////////////////////////////////

const getAdditionalConstraintsUrl = (
  studyId: StudyMetadata["id"],
  areaId: Area["name"],
  storageId: Storage["id"],
): string => `/v1/studies/${studyId}/areas/${areaId}/storages/${storageId}/additional-constraints`;

const getAdditionalConstraintUrl = (
  studyId: StudyMetadata["id"],
  areaId: Area["name"],
  storageId: Storage["id"],
  constraintId: string,
): string => `${getAdditionalConstraintsUrl(studyId, areaId, storageId)}/${constraintId}`;

////////////////////////////////////////////////////////////////
// API Functions
////////////////////////////////////////////////////////////////

export async function getAdditionalConstraints(
  studyId: StudyMetadata["id"],
  areaId: Area["name"],
  storageId: Storage["id"],
): Promise<AdditionalConstraint[]> {
  const res = await client.get<AdditionalConstraint[]>(
    getAdditionalConstraintsUrl(studyId, areaId, storageId),
  );
  return res.data;
}

export async function getAdditionalConstraint(
  studyId: StudyMetadata["id"],
  areaId: Area["name"],
  storageId: Storage["id"],
  constraintId: string,
): Promise<AdditionalConstraint> {
  const res = await client.get<AdditionalConstraint>(
    getAdditionalConstraintUrl(studyId, areaId, storageId, constraintId),
  );
  return res.data;
}

export async function createAdditionalConstraint(
  studyId: StudyMetadata["id"],
  areaId: Area["name"],
  storageId: Storage["id"],
  data: CreateAdditionalConstraintParams,
): Promise<AdditionalConstraint> {
  const res = await client.post<AdditionalConstraint[]>(
    getAdditionalConstraintsUrl(studyId, areaId, storageId),
    [
      {
        name: data.name,
        variable: data.variable,
        operator: data.bounds,
        enabled: data.enabled ?? true,
        hours: data.hours,
      },
    ],
  );
  return res.data[0];
}

export async function updateAdditionalConstraint(
  studyId: StudyMetadata["id"],
  areaId: Area["name"],
  storageId: Storage["id"],
  constraintId: string,
  data: Partial<AdditionalConstraint>,
): Promise<AdditionalConstraint> {
  const res = await client.put<AdditionalConstraint>(
    getAdditionalConstraintUrl(studyId, areaId, storageId, constraintId),
    data,
  );
  return res.data;
}

export async function deleteAdditionalConstraint(
  studyId: StudyMetadata["id"],
  areaId: Area["name"],
  // storageId: Storage["id"],
  constraintId: string,
): Promise<void> {
  // TODO: Update API to also use the storageId for consistency
  await client.delete(`/v1/studies/${studyId}/areas/${areaId}/storages/additional-constraints/`, {
    params: { id: constraintId },
  });
}
