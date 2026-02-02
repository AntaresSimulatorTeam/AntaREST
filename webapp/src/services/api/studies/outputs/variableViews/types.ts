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

import type { Frequency } from "@/routes/_authenticated/studies/$studyId/explore/outputs/$outputId/-utils";

export interface ThermalClusterVariablesDTO {
  name: string;
  variables: string[];
}

export interface RenewableClusterVariablesDTO {
  name: string;
  variables: string[];
}

export interface ShortTermStorageVariablesDTO {
  name: string;
  variables: string[];
}

export interface AreaVariablesDTO {
  name: string;
  variables: string[];
  thermalClusters?: ThermalClusterVariablesDTO[];
  renewableClusters?: RenewableClusterVariablesDTO[];
  shortTermStorages?: ShortTermStorageVariablesDTO[];
}

export interface LinkVariablesDTO {
  area1Name: string;
  area2Name: string;
  variables: string[];
}

export interface VariablesListDataDTO {
  areas: AreaVariablesDTO[];
  links: LinkVariablesDTO[];
}

/**
 * Variables List DTO - Response from /v1/studies/{uuid}/output/{output_id}/variables-list
 * This response contains both mcInd and mcAll data structures in a single API call.
 * Variable-per-variable views in the front-end only use mcInd.
 */
export interface VariablesListDTO {
  mcInd: VariablesListDataDTO;
  mcAll: VariablesListDataDTO;
}

export interface VariableViewMatrixDTO {
  data: number[][];
  columns: string[];
  index: string[];
}

export interface MaterializationTaskDTO {
  taskId: string;
}

interface VariableViewBaseParams {
  variableName: string;
  frequency: Frequency;
}

export type VariableViewParams =
  | (VariableViewBaseParams & { type: "area"; areaId: string })
  | (VariableViewBaseParams & { type: "link"; areaFromId: string; areaToId: string })
  | (VariableViewBaseParams & { type: "thermal"; areaId: string; clusterId: string })
  | (VariableViewBaseParams & { type: "renewable"; areaId: string; clusterId: string })
  | (VariableViewBaseParams & { type: "st_storage"; areaId: string; clusterId: string });

interface VariableViewBaseParamsDTO {
  variable_name: string;
  frequency: Frequency;
}

export type VariableViewParamsDTO =
  | (VariableViewBaseParamsDTO & { type: "area"; area_id: string })
  | (VariableViewBaseParamsDTO & { type: "link"; area_from_id: string; area_to_id: string })
  | (VariableViewBaseParamsDTO & { type: "thermal"; area_id: string; thermal_id: string })
  | (VariableViewBaseParamsDTO & { type: "renewable"; area_id: string; renewable_id: string })
  | (VariableViewBaseParamsDTO & { type: "st_storage"; area_id: string; storage_id: string });

export interface GetVariablesListParams {
  studyId: string;
  outputId: string;
}

export interface GetTimeIndexParams {
  studyId: string;
  outputId: string;
  frequency: Frequency;
}

export interface GetVariableViewDataParams {
  studyId: string;
  outputId: string;
  params: VariableViewParams;
}

export interface MaterializeVariableViewParams {
  studyId: string;
  outputId: string;
  params: VariableViewParams;
}
