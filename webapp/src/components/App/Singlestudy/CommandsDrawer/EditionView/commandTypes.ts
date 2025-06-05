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

import type { CommandResultDTO } from "../../../../../types/types";

interface AntaresConfig {
  version: string;
  caption: string;
  created: number;
  lastsave: number;
  author: string;
}

interface CommandArgsData {
  antares: AntaresConfig;
}

export interface CommandArgsDTO {
  data: CommandArgsData;
  target: string;
}

export interface CommandItem {
  id?: string;
  action: string;
  updated: boolean;
  args: CommandArgsDTO | object;
  results?: CommandResultDTO;
  version?: number;
  user?: string;
  updatedAt?: string;
}

export interface JsonCommandItem {
  action: string;
  args: object;
}

export enum CommandEnum {
  CREATE_AREA = "create_area",
  REMOVE_AREA = "remove_area",
  CREATE_DISTRICT = "create_district",
  REMOVE_DISTRICT = "remove_district",
  CREATE_LINK = "create_link",
  REMOVE_LINK = "remove_link",
  CREATE_BINDING_CONSTRAINT = "create_binding_constraint",
  UPDATE_BINDING_CONSTRAINT = "update_binding_constraint",
  REMOVE_BINDING_CONSTRAINT = "remove_binding_constraint",
  CREATE_RENEWABLES_CLUSTER = "create_renewables_cluster",
  REMOVE_RENEWABLES_CLUSTER = "remove_renewables_cluster",
  CREATE_CLUSTER = "create_cluster",
  REMOVE_CLUSTER = "remove_cluster",
  REPLACE_MATRIX = "replace_matrix",
  UPDATE_CONFIG = "update_config",
}

export interface CreateArea {
  area_name: string;
}

export type MatrixData = number;
export enum TimeStep {
  HOURLY = "hourly",
  DAILY = "daily",
  WEEKLY = "weekly",
}

export enum BindingConstraintOperator {
  BOTH = "both",
  EQUAL = "equal",
  GREATER = "greater",
  LESS = "less",
}

export interface CreateBindingConstraint {
  name: string;
  enabled: boolean;
  time_step: TimeStep;
  operator: BindingConstraintOperator;
  coeffs: Record<string, number[]>;
  values?: MatrixData[][] | string;
  comments?: string;
}

export interface CreateCluster {
  area_id: string;
  cluster_name: string;
  parameters: Record<string, string>;
  prepro?: MatrixData[][] | string;
  modulation?: MatrixData[][] | string;
}

export enum DistrictBaseFilter {
  add_all = "add-all",
  remove_all = "remove-all",
}

export interface CreateDistrict {
  name: string;
  base_filter: DistrictBaseFilter;
  filter_items?: string;
  output?: boolean;
  comments?: string;
}

export interface CreateLink {
  area1: string;
  area2: string;
  parameters?: Record<string, string>;
  series?: MatrixData[][] | string;
}

export interface RemoveArea {
  id: string;
}

export interface RemoveBindingConstraint {
  id: string;
}

export interface RemoveCluster {
  area_id: string;
  cluster_id: string;
}

export interface RemoveDistrict {
  id: string;
}

export interface RemoveLink {
  area1: string;
  area2: string;
}

export interface ReplaceMatrix {
  target: string;
  matrix: MatrixData[][] | string;
}

export interface UpdateBindingConstraint {
  id: string;
  enabled: boolean;
  time_step: TimeStep;
  operator: BindingConstraintOperator;
  coeffs: Record<string, number[]>;
  values?: MatrixData[][] | string;
  comments?: string;
}

export interface UpdateConfig {
  target: string;
  data: string | number | boolean | object;
}

export type CommandType =
  | CreateArea
  | CreateBindingConstraint
  | CreateCluster
  | CreateDistrict
  | CreateLink
  | RemoveArea
  | RemoveBindingConstraint
  | RemoveCluster
  | RemoveDistrict
  | RemoveLink
  | ReplaceMatrix
  | UpdateBindingConstraint
  | UpdateConfig;

export default {};
