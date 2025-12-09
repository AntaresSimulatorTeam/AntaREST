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

import type { VARIABLE_VIEW_FREQUENCIES } from "./constants";

////////////////////////////////////////////////////////////////
// Derived Types
////////////////////////////////////////////////////////////////

export type VariableViewFrequency = (typeof VARIABLE_VIEW_FREQUENCIES)[number];

////////////////////////////////////////////////////////////////
// API DTO Types
////////////////////////////////////////////////////////////////

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

export interface TimeIndexDTO {
  startDate: string;
  steps: number;
  firstWeekSize: number;
  level: VariableViewFrequency;
}

export interface VariableViewMatrixDTO {
  data: number[][];
  columns: string[];
  index: string[];
}

export interface MaterializationTaskDTO {
  taskId: string;
}

////////////////////////////////////////////////////////////////
// Request Params
////////////////////////////////////////////////////////////////

interface VariableViewBaseParams {
  variableName: string;
  frequency: VariableViewFrequency;
}

export interface AreaVariableViewParams extends VariableViewBaseParams {
  type: "area";
  areaId: string;
}

export interface LinkVariableViewParams extends VariableViewBaseParams {
  type: "link";
  areaFromId: string;
  areaToId: string;
}

export interface ThermalClusterVariableViewParams extends VariableViewBaseParams {
  type: "thermal";
  areaId: string;
  clusterId: string;
}

export interface RenewableClusterVariableViewParams extends VariableViewBaseParams {
  type: "renewable";
  areaId: string;
  clusterId: string;
}

export interface ShortTermStorageVariableViewParams extends VariableViewBaseParams {
  type: "st_storage";
  areaId: string;
  clusterId: string;
}

export type VariableViewParams =
  | AreaVariableViewParams
  | LinkVariableViewParams
  | ThermalClusterVariableViewParams
  | RenewableClusterVariableViewParams
  | ShortTermStorageVariableViewParams;
