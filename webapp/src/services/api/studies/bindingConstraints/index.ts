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

import { format } from "@/utils/stringUtils";
import client from "../../client";
import { getStudyMetadata } from "../../study";
import {
  adaptBindingConstraintDtoToBindingConstraint,
  adaptBindingConstraintOperationDtoToStudyVersion,
} from "./adapters";
import type {
  BindingConstraintDTO,
  CreateBindingConstraintsParams,
  DeleteBindingConstraintParams,
  DuplicateBindingConstraintParams,
  GetBindingConstraintParams,
  GetBindingConstraintsParams,
  UpdateBindingConstraintsParams,
} from "./type";

const BASE_URL = "/v1/studies/{studyId}/bindingconstraints";
const BINDING_CONSTRAINT_URL = `${BASE_URL}/{constraintId}`;

export async function getBindingConstraint({ studyId, constraintId }: GetBindingConstraintParams) {
  const url = format(BINDING_CONSTRAINT_URL, { studyId, constraintId });
  const { data } = await client.get<BindingConstraintDTO>(url);
  return adaptBindingConstraintDtoToBindingConstraint(data);
}

export async function getBindingConstraints({ studyId, filters }: GetBindingConstraintsParams) {
  const url = format(BASE_URL, { studyId });
  const { data } = await client.get<BindingConstraintDTO[]>(url, { params: filters });
  return data.map(adaptBindingConstraintDtoToBindingConstraint);
}

export async function createBindingConstraint({ studyId, values }: CreateBindingConstraintsParams) {
  const url = format(BASE_URL, { studyId });
  const study = await getStudyMetadata(studyId);
  const adaptedValues = adaptBindingConstraintOperationDtoToStudyVersion(values, study.version);

  const { data } = await client.post<BindingConstraintDTO>(url, adaptedValues);

  return adaptBindingConstraintDtoToBindingConstraint(data);
}

export async function updateBindingConstraint({
  studyId,
  constraintId,
  values,
}: UpdateBindingConstraintsParams) {
  const url = format(BINDING_CONSTRAINT_URL, { studyId, constraintId });
  const study = await getStudyMetadata(studyId);
  const adaptedValues = adaptBindingConstraintOperationDtoToStudyVersion(values, study.version);

  const { data } = await client.put<BindingConstraintDTO>(url, adaptedValues);

  return adaptBindingConstraintDtoToBindingConstraint(data);
}

export async function duplicateBindingConstraint({
  studyId,
  constraintId,
  newConstraintName,
}: DuplicateBindingConstraintParams) {
  const url = format(BINDING_CONSTRAINT_URL, { studyId, constraintId });

  const { data } = await client.post<BindingConstraintDTO>(url, null, {
    params: { new_constraint_name: newConstraintName },
  });

  return adaptBindingConstraintDtoToBindingConstraint(data);
}

export async function deleteBindingConstraint({
  studyId,
  constraintId,
}: DeleteBindingConstraintParams) {
  const url = format(BINDING_CONSTRAINT_URL, { studyId, constraintId });
  const { data } = await client.delete<string>(url);
  return data;
}
