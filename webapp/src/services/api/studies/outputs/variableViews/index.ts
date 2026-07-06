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
import type { MatrixIndex } from "@/types/types";
import { sanitizeJsonResponse } from "@/utils/apiUtils";
import { adaptVariableViewParamsToDto } from "./adapters";
import type {
  ExportVariableViewParams,
  GetTimeIndexParams,
  GetVariablesListParams,
  GetVariableViewDataParams,
  MaterializeVariableViewParams,
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
  // return data;

  return {
    mcInd: {
      areas: [
        {
          name: "areain-1",
          variables: ["A. DEMAND", "A. GEN", "Z. LOAD"],
          thermalClusters: [
            {
              name: "cluster in2",
              variables: ["TC1. GEN", "TC1. COST"],
            },
          ],
          renewableClusters: [
            {
              name: "ren1",
              variables: ["RC1. GEN", "RC1. COST"],
            },
          ],
          shortTermStorages: [
            {
              name: "stor1",
              variables: ["STS1. GEN", "STS1. COST"],
            },
          ],
        },
      ],
      links: [
        {
          area1Name: "areain-1",
          area2Name: "areain-2",
          variables: ["L. FLOW", "L. LOSS"],
        },
      ],
    },
    mcAll: {
      areas: [],
      links: [],
    },
  } satisfies VariablesListDTO;
}

////////////////////////////////////////////////////////////////
// Variable View Data
////////////////////////////////////////////////////////////////

export async function getOutputMatrixIndex({ studyId, outputId, frequency }: GetTimeIndexParams) {
  const { data } = await client.get<MatrixIndex>(
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
    {
      params: queryParams,
      // Custom transformer to handle NaN values from backend
      // The backend sends invalid JSON with literal NaN tokens that must be sanitized
      transformResponse: [sanitizeJsonResponse],
    },
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

////////////////////////////////////////////////////////////////
// Export
////////////////////////////////////////////////////////////////

export async function exportVariableViewData({
  studyId,
  outputId,
  params,
  format,
  header,
  index,
}: ExportVariableViewParams) {
  const queryParams = adaptVariableViewParamsToDto(params);
  const { data } = await client.get<Blob>(
    `/v1/studies/${studyId}/output/${outputId}/variables-views/export`,
    {
      params: { ...queryParams, export_format: format, header, index },
      responseType: "blob",
    },
  );
  return data;
}
