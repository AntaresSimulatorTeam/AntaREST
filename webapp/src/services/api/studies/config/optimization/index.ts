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
import { adaptOptimizationDtoToForm, adaptOptimizationFormToDto } from "./adapters";
import type {
  BaseOptimizationParams,
  GetOptimizationFormParams,
  OptimizationDTO,
  SetOptimizationFormParams,
  SetOptimizationParams,
} from "./types";

const URL = "/v1/studies/{studyId}/config/optimization/form";

export async function getOptimization({ studyId }: BaseOptimizationParams) {
  const { data } = await client.get<OptimizationDTO>(format(URL, { studyId }));
  return data;
}

export async function setOptimization({ studyId, values }: SetOptimizationParams) {
  const { data } = await client.put<OptimizationDTO>(format(URL, { studyId }), values);
  return data;
}

export async function getOptimizationForm({ studyId, studyVersion }: GetOptimizationFormParams) {
  const dto = await getOptimization({ studyId });
  return adaptOptimizationDtoToForm(dto, studyVersion);
}

export async function setOptimizationForm({
  studyId,
  values,
  studyVersion,
}: SetOptimizationFormParams) {
  const dto = await setOptimization({ studyId, values: adaptOptimizationFormToDto(values) });
  return adaptOptimizationDtoToForm(dto, studyVersion);
}
