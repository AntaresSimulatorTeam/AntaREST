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

import type {
  MONTE_CARLO_MODES,
  VARIABLE_VIEW_EXPORT_FORMATS,
  VARIABLE_VIEW_FREQUENCIES,
  VARIABLE_VIEW_OBJECT_TYPES,
} from "./constants";

////////////////////////////////////////////////////////////////
// Derived Types
////////////////////////////////////////////////////////////////

export type VariableViewFrequency = (typeof VARIABLE_VIEW_FREQUENCIES)[number];
export type VariableViewObjectType = (typeof VARIABLE_VIEW_OBJECT_TYPES)[number];
export type VariableViewExportFormat = (typeof VARIABLE_VIEW_EXPORT_FORMATS)[number];
export type MonteCarloMode = (typeof MONTE_CARLO_MODES)[number];

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
  linkId: string;
}

export interface ThermalClusterVariableViewParams extends VariableViewBaseParams {
  type: "thermal_cluster";
  areaId: string;
  clusterId: string;
}

export interface RenewableClusterVariableViewParams extends VariableViewBaseParams {
  type: "renewable_cluster";
  areaId: string;
  clusterId: string;
}

export interface ShortTermStorageVariableViewParams extends VariableViewBaseParams {
  type: "short_term_storage";
  areaId: string;
  clusterId: string;
}

export type VariableViewParams =
  | AreaVariableViewParams
  | LinkVariableViewParams
  | ThermalClusterVariableViewParams
  | RenewableClusterVariableViewParams
  | ShortTermStorageVariableViewParams;

////////////////////////////////////////////////////////////////
// UI Types
////////////////////////////////////////////////////////////////

export interface SelectedVariableObject {
  type: VariableViewObjectType;
  areaId?: string;
  linkId?: string;
  clusterId?: string;
  label: string;
}

export interface VariablePerVariableState {
  mode: MonteCarloMode;
  selectedObject: SelectedVariableObject | null;
  selectedVariable: string;
  selectedFrequency: VariableViewFrequency;
  isViewMaterialized: boolean;
  isProcessing: boolean;
  materializationTaskId: string | null;
}
