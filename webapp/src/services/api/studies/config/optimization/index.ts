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
  BaseOptimizationParams,
  OptimizationFormFields,
  SetOptimizationParams,
} from "./types";

const URL = "/v1/studies/{studyId}/config/optimization/form";

export async function getOptimizationFormFields({ studyId }: BaseOptimizationParams) {
  const { data } = await client.get<OptimizationFormFields>(format(URL, { studyId }));
  return data;
}

export async function setOptimizationFormFields({ studyId, values }: SetOptimizationParams) {
  const { data } = await client.put<OptimizationFormFields>(format(URL, { studyId }), values);
  return data;
}
