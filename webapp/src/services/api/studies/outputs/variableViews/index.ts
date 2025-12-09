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
import { adaptVariableViewParamsToDto } from "./adapters";
import type {
  GetTimeIndexParams,
  GetVariableViewDataParams,
  GetVariablesListParams,
  MaterializeVariableViewParams,
  TimeIndexDTO,
  VariablesListDTO,
  VariableViewMatrixDTO,
} from "./types";

////////////////////////////////////////////////////////////////
// Variables List
////////////////////////////////////////////////////////////////

export async function getVariablesList({ studyId, outputId }: GetVariablesListParams) {
  const { data } = await client.get<VariablesListDTO>(
    `/v1/studies/${studyId}/output/${outputId}/variables-list`,
  );
  return data;
}

////////////////////////////////////////////////////////////////
// Variable View Data
////////////////////////////////////////////////////////////////

export async function getTimeIndex({ studyId, outputId, frequency }: GetTimeIndexParams) {
  const { data } = await client.get<TimeIndexDTO>(
    `/v1/studies/${studyId}/output/${outputId}/time-index`,
    { params: { frequency } },
  );
  return data;
}

export async function getVariableViewData({
  studyId,
  outputId,
  params,
}: GetVariableViewDataParams) {
  const queryParams = adaptVariableViewParamsToDto(params);
  const { data } = await client.get<VariableViewMatrixDTO>(
    `/v1/studies/${studyId}/output/${outputId}/variables-views/data`,
    { params: queryParams },
  );
  return data;
}

////////////////////////////////////////////////////////////////
// Materialization
////////////////////////////////////////////////////////////////

export async function materializeVariableView({
  studyId,
  outputId,
  params,
}: MaterializeVariableViewParams) {
  const queryParams = adaptVariableViewParamsToDto(params);
  const { data } = await client.post<string>(
    `/v1/studies/${studyId}/output/${outputId}/variables-views/materialize`,
    null,
    { params: queryParams },
  );

  return data;
}
