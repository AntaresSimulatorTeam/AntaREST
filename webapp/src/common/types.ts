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

import type { TaskTypeValue } from "../services/api/tasks/types";

export type IdType = number | string;

export interface IdentityDTO<T extends IdType = string> {
  id: T;
  name: string;
}

export type StudyPublicMode = "NONE" | "READ" | "EXECUTE" | "EDIT" | "FULL";

export interface GenericInfo {
  id: IdType;
  name: string;
}

export interface SynthesisSummary {
  study_id: string;
}

export interface StudyMetadataOwner {
  id?: number;
  name: string;
}

export enum StudyType {
  VARIANT = "variantstudy",
  RAW = "rawstudy",
}

export interface StudyMetadataDTO extends IdentityDTO {
  owner: StudyMetadataOwner;
  type: StudyType;
  created: string;
  updated: string;
  version: number;
  workspace: string;
  managed: boolean;
  archived: boolean;
  groups: IdentityDTO[];
  public_mode: StudyPublicMode;
  folder?: string;
  horizon?: string;
  tags?: string[];
}

export interface StudyMetadata {
  id: string;
  name: string;
  creationDate: string;
  modificationDate: string;
  owner: StudyMetadataOwner;
  type: StudyType;
  version: string;
  workspace: string;
  managed: boolean;
  archived: boolean;
  groups: Array<{ id: string; name: string }>;
  publicMode: StudyPublicMode;
  folder?: string;
  horizon?: string;
  tags?: string[];
}

export interface StudyMetadataPatchDTO {
  name?: string;
  author?: string;
  horizon?: string;
  tags?: string[];
}

export interface StudyOutput {
  name: string;
  type: string;
  completionDate: string;
  status: string;
  archived: boolean;
}

export interface StudyLayer {
  areas: string[];
  id: string;
  name: string;
}

export interface VariantTreeDTO {
  node: StudyMetadataDTO;
  children: VariantTreeDTO[];
}

export interface VariantTree {
  node: StudyMetadata;
  children: VariantTree[];
}

export interface AdequacyPatchParams {
  legacy?: boolean;
}

export interface XpansionParams {
  enabled: boolean;
  sensitivity_mode?: boolean;
  output_id?: string;
}

export interface LaunchOptions {
  xpansion?: XpansionParams;
  xpansion_r_version?: boolean;
  nb_cpu?: number;
  time_limit?: number;
  post_processing?: boolean;
  adequacy_patch?: AdequacyPatchParams;
  output_suffix?: string;
  other_options?: string;
  auto_unzip?: boolean;
}

export type JobStatus = "running" | "pending" | "success" | "failed";

export interface LaunchJob {
  id: string;
  studyId: string;
  status: JobStatus;
  creationDate: string;
  completionDate: string;
  launcherParams?: LaunchOptions;
  msg: string;
  outputId: string;
  exitCode: number;
}

export interface LaunchJobDTO {
  id: string;
  study_id: string;
  status: JobStatus;
  creation_date: string;
  completion_date: string;
  launcher_params: string;
  msg: string;
  output_id: string;
  exit_code: number;
}

export interface LaunchJobProgressDTO {
  id: string;
  progress: number;
  message: string;
}

export type LaunchJobsProgress = Record<string, number>;

export enum RoleType {
  ADMIN = 40,
  WRITER = 30,
  RUNNER = 20,
  READER = 10,
}

export interface RoleDTO {
  group_id: string;
  group_name: string;
  identity_id: number;
  type: RoleType;
}

export interface RoleCreationDTO {
  group_id: string;
  identity_id: number;
  type: RoleType;
}

export type UserDTO = IdentityDTO<number>;

export interface UserDetailsDTO extends UserDTO {
  roles: RoleDTO[];
}

export interface UserRoleDTO extends IdentityDTO<number> {
  role: RoleType;
}

export type GroupDTO = IdentityDTO;

export interface GroupDetailsDTO extends GroupDTO {
  users: UserRoleDTO[];
}

export interface RoleDetailsDTO {
  group: GroupDTO;
  identity: UserDTO;
  type: RoleType;
}

export interface JWTGroup {
  id: string;
  name: string;
  role: RoleType;
}

export interface UserInfo {
  user: string;
  groups: JWTGroup[];
  id: number;
  impersonator: number;
  type: string;
  accessToken: string;
  refreshToken: string;
  expirationDate?: number;
}

export interface RefreshDTO {
  access_token: string;
  refresh_token: string;
  user: number;
}

export interface BotDTO extends IdentityDTO<number> {
  owner: number;
  is_author: boolean;
}

export interface BotDetailsDTO extends BotDTO {
  roles: RoleDTO[];
}

export interface BotRoleCreateDTO {
  group: string;
  role: RoleType;
}

export interface BotCreateDTO {
  name: string;
  is_author: boolean;
  roles: BotRoleCreateDTO[];
}

export interface UserToken {
  user: UserDTO;
  bots: BotDTO[];
}

export interface MatrixType {
  columns: string[];
  index: Array<string | number>;
  data: number[][];
}

export type MatrixInfoDTO = IdentityDTO;

export interface MatrixDataSetDTO extends IdentityDTO {
  public: boolean;
  groups: GroupDTO[];
  matrices: MatrixInfoDTO[];
  owner: {
    id: number;
    name: string;
  };
  created_at: string;
  updated_at: string;
}

export interface MatrixDataSetUpdateDTO {
  name: string;
  groups: string[];
  public: boolean;
}

export interface MatrixDTO {
  id: string;
  width: number;
  height: number;
  index: string[];
  columns: string[];
  data: number[][];
  created_at: number;
}

export interface CommandDTO {
  id?: string;
  action: string;
  args: object;
  version?: number;
  user_name?: string;
  updated_at?: string;
}

export type Components = Record<string, () => React.ReactNode>;

export interface CommandResultDTO {
  study_id: string;
  id: string;
  success: boolean;
  message: string;
}

export interface Cluster {
  id: string;
  name: string;
  enabled: boolean;
}

export interface Link {
  filters_synthesis: string[];
  filters_year: string[];
}

export interface Area {
  name: string;
  links: Record<string, Link>;
  thermals: Cluster[];
  renewables: Cluster[];
  filters_synthesis: string[];
  filters_year: string[];
}

export interface Set {
  name?: string;
  inverted_set: boolean;
  areas?: string[];
  output: boolean;
  filters_synthesis: string[];
  filters_year: string[];
}

export interface Simulation {
  name: string;
  date: string;
  mode: string;
  nbyears: number;
  synthesis: boolean;
  by_year: boolean;
  error: boolean;
}

export interface FileStudyTreeConfigDTO {
  study_path: string;
  path: string;
  study_id: string;
  version: number;
  output_path?: string;
  areas: Record<string, Area>;
  sets: Record<string, Set>;
  outputs: Record<string, Simulation>;
  bindings: string[];
  store_new_set: boolean;
  archive_input_series: string[];
  enr_modelling: string;
}

export interface LinkElement {
  id: string;
  label: string;
  name: string;
  area1: string;
  area2: string;
}

export interface ClusterElement {
  area: string;
  cluster: string;
}

export interface LinkClusterElement {
  id: string;
  name: string;
}

export interface LinkClusterItem {
  element: LinkClusterElement;
  item_list: LinkClusterElement[];
}

export interface AllClustersAndLinks {
  links: LinkClusterItem[];
  clusters: LinkClusterItem[];
}

export type LinkListElement = Record<string, LinkElement>;

export enum StudyOutputDownloadType {
  LINKS = "LINK",
  DISTRICT = "DISTRICT",
  AREAS = "AREA",
}

export enum StudyOutputDownloadLevelDTO {
  ANNUAL = "annual",
  MONTHLY = "monthly",
  WEEKLY = "weekly",
  DAILY = "daily",
  HOURLY = "hourly",
}

export interface StudyOutputDownloadDTO {
  type: StudyOutputDownloadType;
  years?: number[];
  level: StudyOutputDownloadLevelDTO;
  filterIn?: string;
  filterOut?: string;
  filter?: string[];
  columns?: string[];
  synthesis: boolean;
  includeClusters: boolean;
}

export interface MatrixIndex {
  start_date: string;
  steps: number;
  first_week_size: number;
  level: StudyOutputDownloadLevelDTO;
}

export enum MatrixStats {
  TOTAL = "total",
  STATS = "stats",
  NOCOL = "",
}

export enum Operator {
  ADD = "+",
  SUB = "-",
  MUL = "*",
  DIV = "/",
  ABS = "ABS",
  EQ = "=",
}

export interface MatrixSliceDTO {
  row_from: number;
  row_to: number;
  column_from: number;
  column_to: number;
}

export interface MatrixOperationDTO {
  operation: Operator;
  value: number;
}

export interface MatrixBaseEditDTO {
  operation: MatrixOperationDTO;
}

export interface MatrixSliceEditDTO extends MatrixBaseEditDTO {
  slices: MatrixSliceDTO[];
}

export interface MatrixSingleEditDTO extends MatrixBaseEditDTO {
  coordinates: number[][];
}

export type MatrixEditDTO = MatrixSliceDTO | MatrixSingleEditDTO;

export interface MatrixAggregationResult {
  index: MatrixIndex;
  data: Record<string, Record<string, Record<string, number[]>>>;
  warnings: string[];
}

export type LinkSynthesis = Record<string, object>;

export interface AreasSynthesis {
  name: string;
  links: LinkSynthesis;
  thermals: string;
  renewables: string[];
  filters_synthesis: string[];
  filters_year: string[];
}

export type AreasNameSynthesis = Record<string, AreasSynthesis>;

export interface LinkProperties {
  source: string;
  target: string;
  temp?: boolean;
}

export type AreaLayerColor = Record<string, string>;
export type AreaLayerPosition = Record<string, number>;

export interface AreaUI {
  id: string;
  color_b: number;
  color_g: number;
  color_r: number;
  layers: string;
  x: number;
  y: number;
}

export interface SingleAreaConfig {
  layerColor?: AreaLayerColor;
  layerX?: AreaLayerPosition;
  layerY?: AreaLayerPosition;
  ui: AreaUI;
}

export type AreasConfig = Record<string, SingleAreaConfig>;

export interface UpdateAreaUi {
  x: number;
  y: number;
  color_rgb: number[];
  layerX: AreaLayerPosition;
  layerY: AreaLayerPosition;
  layerColor: AreaLayerColor;
}

export interface AreaCreationDTO {
  name: string;
  type: object;
  metadata?: object;
  set?: string[];
}

export interface AreaInfoDTO extends AreaCreationDTO {
  id: string;
  thermals: object[];
}

export interface TaskView {
  id: string;
  name: React.ReactNode;
  dateView: React.ReactNode;
  action: React.ReactNode;
  date: string;
  type: TaskTypeValue | "DOWNLOAD" | "LAUNCH" | "UNKNOWN";
  status: string;
}

export type ValidationReturn = string | true;

export interface MatrixConfig {
  url: string;
  titleKey: string;
  columnsNames?: string[];
}

export interface SplitMatrixContent {
  type: "split";
  matrices: [MatrixConfig, MatrixConfig];
}

export interface SingleMatrixContent {
  type: "single";
  matrix: MatrixConfig;
}

export interface MatrixItem {
  titleKey: string;
  content: SplitMatrixContent | SingleMatrixContent;
}
