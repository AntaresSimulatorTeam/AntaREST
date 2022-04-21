/* eslint-disable camelcase */
import { Moment } from "moment";
import { ReactNode } from "react";

export type IDType = number | string;

export enum SortElement {
  DATE = "DATE",
  NAME = "NAME",
}

export enum SortStatus {
  INCREASE = "INCREASE",
  DECREASE = "DECREASE",
}

export interface SortItem {
  element: SortElement;
  status: SortStatus;
}

export type StudyDataType = "json" | "file" | "matrixfile" | "matrix";

export type StudyPublicMode = "NONE" | "READ" | "EXECUTE" | "EDIT" | "FULL";

export interface GenericInfo {
  id: IDType;
  name: string;
}

export interface StudySummary {
  id: string;
  name: string;
  workspace: string;
}

export interface StudyMetadataOwner {
  id?: number;
  name: string;
}

export type StudyType = "variantstudy" | "rawstudy";

export interface StudyMetadataDTO {
  id: string;
  owner: StudyMetadataOwner;
  name: string;
  type: StudyType;
  created: string;
  updated: string;
  version: number;
  workspace: string;
  managed: boolean;
  archived: boolean;
  groups: Array<{ id: string; name: string }>;
  public_mode: StudyPublicMode;
  folder?: string;
  horizon?: string;
  scenario?: string;
  status?: string;
  doc?: string;
  tags?: Array<string>;
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
  scenario?: string;
  status?: string;
  doc?: string;
  tags?: Array<string>;
}

export interface StudyMetadataPatchDTO {
  horizon?: string;
  scenario?: string;
  status?: string;
  doc?: string;
  tags?: Array<string>;
}

export interface StudyOutput {
  name: string;
  type: string;
  completionDate: string;
  referenceStatus: boolean;
  synchronized: boolean;
  status: string;
}

export interface VariantTreeDTO {
  node: StudyMetadataDTO;
  children: Array<VariantTreeDTO>;
}

export interface VariantTree {
  node: StudyMetadata;
  children: Array<VariantTree>;
}

export type JobStatus = "running" | "pending" | "success" | "failed";

export interface LaunchJob {
  id: string;
  studyId: string;
  status: JobStatus;
  creationDate: string;
  completionDate: string;
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
  msg: string;
  output_id: string;
  exit_code: number;
}

export enum RoleType {
  ADMIN = 40,
  RUNNER = 30,
  WRITER = 20,
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

export interface UserDTO {
  id: number;
  name: string;
}

export interface UserRoleDTO {
  id: number;
  name: string;
  role: RoleType;
}

export interface GroupDTO {
  id: string;
  name: string;
}

export interface JWTGroup {
  id: string;
  name: string;
  role: RoleType;
}

export interface UserInfo {
  user: string;
  groups: Array<JWTGroup>;
  id: number;
  impersonator: number;
  type: string;
  accessToken: string;
  refreshToken: string;
  expirationDate?: Moment;
}

export interface Identity {
  id: number;
  name: string;
  type: string;
}

export interface IdentityDTO {
  id: number;
  name: string;
  roles: Array<RoleDTO>;
}

export interface BotDTO {
  id: number;
  name: string;
  owner: number;
  isAuthor: boolean;
}

export interface BotRoleCreateDTO {
  group: string;
  role: RoleType;
}

export interface BotCreateDTO {
  name: string;
  is_author: boolean;
  roles: Array<BotRoleCreateDTO>;
}

export interface BotIdentityDTO {
  id: number;
  name: string;
  isAuthor: boolean;
  roles: Array<RoleDTO>;
}

export interface UserToken {
  user: UserDTO;
  bots: Array<BotDTO>;
}

export interface UserGroup {
  group: GroupDTO;
  users: Array<UserRoleDTO>;
}

export interface MatrixType {
  columns: Array<string>;
  index: Array<string | number>;
  data: Array<Array<number>>;
}

export interface MatrixInfoDTO {
  id: string;
  name: string;
}

export interface MatrixDataSetDTO {
  id: string;
  name: string;
  public: boolean;
  groups: Array<GroupDTO>;
  matrices: Array<MatrixInfoDTO>;
  owner: {
    id: number;
    name: string;
  };
  created_at: string;
  updated_at: string;
}

export interface MatrixDataSetUpdateDTO {
  name: string;
  groups: Array<string>;
  public: boolean;
}

export interface MatrixDTO {
  width: number;
  height: number;
  index: Array<string>;
  columns: Array<string>;
  data: Array<Array<number>>;
  created_at: number;
  id: string;
}

export interface CommandDTO {
  id?: string;
  action: string;
  args: object;
}

export enum WSEvent {
  STUDY_CREATED = "STUDY_CREATED",
  STUDY_DELETED = "STUDY_DELETED",
  STUDY_EDITED = "STUDY_EDITED",
  STUDY_JOB_STARTED = "STUDY_JOB_STARTED",
  STUDY_JOB_LOG_UPDATE = "STUDY_JOB_LOG_UPDATE",
  STUDY_JOB_COMPLETED = "STUDY_JOB_COMPLETED",
  STUDY_JOB_STATUS_UPDATE = "STUDY_JOB_STATUS_UPDATE",
  STUDY_VARIANT_GENERATION_COMMAND_RESULT = "STUDY_VARIANT_GENERATION_COMMAND_RESULT",
  TASK_ADDED = "TASK_ADDED",
  TASK_RUNNING = "TASK_RUNNING",
  TASK_COMPLETED = "TASK_COMPLETED",
  TASK_FAILED = "TASK_FAILED",
  DOWNLOAD_CREATED = "DOWNLOAD_CREATED",
  DOWNLOAD_READY = "DOWNLOAD_READY",
  DOWNLOAD_EXPIRED = "DOWNLOAD_EXPIRED",
  DOWNLOAD_FAILED = "DOWNLOAD_FAILED",
  MESSAGE_INFO = "MESSAGE_INFO",
  MAINTENANCE_MODE = "MAINTENANCE_MODE",
}

export enum DefaultFilterKey {
  USERS = "v2.studylisting.filter.user",
  GROUPS = "v2.studylisting.filter.group",
  VERSIONS = "v2.studylisting.filter.version",
  MANAGED = "v2.studylisting.filter.managed",
  SORTING = "v2.studylisting.filter.sorting",
  FOLDER = "v2.studylisting.filter.folder",
  FAVORITE_STUDIES = "v2.studylisting.favorite",
  TAGS = "v2.studylisting.filter.tag",
}

export interface WSMessage {
  type: string;
  payload: unknown;
}

export interface WSLogMessage {
  log: string;
  job_id: string;
  study_id: string;
}

export type Components = {
  [item: string]: () => ReactNode;
};

export interface CommandResultDTO {
  study_id: string;
  id: string;
  success: boolean;
  message: string;
}

export interface TaskResult {
  success: boolean;
  message: string;
  return_value?: string;
}

export interface TaskLogDTO {
  id: string;
  message: string;
}

export enum TaskStatus {
  PENDING = 1,
  RUNNING = 2,
  COMPLETED = 3,
  FAILED = 4,
  TIMEOUT = 5,
  CANCELLED = 6,
}

export enum TaskType {
  LAUNCH = "LAUNCH",
  EXPORT = "EXPORT",
  VARIANT_GENERATION = "VARIANT_GENERATION",
  COPY = "COPY",
  ARCHIVE = "ARCHIVE",
  UNARCHIVE = "UNARCHIVE",
  DOWNLOAD = "DOWNLOAD",
  SCAN = "SCAN",
  UNKNOWN = "UNKNOWN",
}

export interface TaskDTO {
  id: string;
  name: string;
  owner?: number;
  status: TaskStatus;
  creation_date_utc: string;
  completion_date_utc?: string;
  result?: TaskResult;
  logs?: Array<TaskLogDTO>;
  type?: TaskType;
  ref_id?: string;
}

export interface TaskEventPayload {
  id: string;
  message: string;
}

export interface Cluster {
  id: string;
  name: string;
  enabled: boolean;
}

export interface Link {
  filters_synthesis: Array<string>;
  filters_year: Array<string>;
}

export interface Area {
  name: string;
  links: { [elm: string]: Link };
  thermals: Array<Cluster>;
  renewables: Array<Cluster>;
  filters_synthesis: Array<string>;
  filters_year: Array<string>;
}
export interface Set {
  name?: string;
  inverted_set: boolean;
  areas?: Array<string>;
  output: boolean;
  filters_synthesis: Array<string>;
  filters_year: Array<string>;
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
  areas: { [elm: string]: Area };
  sets: { [elm: string]: Set };
  outputs: { [elm: string]: Simulation };
  bindings: Array<string>;
  store_new_set: boolean;
  archive_input_series: Array<string>;
  enr_modelling: string;
}

export enum StudyOutputDownloadType {
  LINK = "LINK",
  DISTRICT = "DISTRICT",
  AREA = "AREA",
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
  years?: Array<number>;
  level: StudyOutputDownloadLevelDTO;
  filterIn?: string;
  filterOut?: string;
  filter?: Array<string>;
  columns?: Array<string>;
  synthesis: boolean;
  includeClusters: boolean;
}

export interface MatrixIndex {
  start_date: string;
  steps: number;
  first_week_size: number;
  level: StudyOutputDownloadLevelDTO;
}

export interface MatrixAggregationResult {
  index: MatrixIndex;
  data: {
    [id: string]: {
      [elm: string]: {
        [item: string]: Array<number>;
      };
    };
  };
  warnings: Array<string>;
}

export interface NodeProperties {
  id: string;
  name: string;
  x: number;
  y: number;
  color: string;
  rgbColor: Array<number>;
  size: { width: number; height: number };
  highlighted?: boolean;
}

export interface LinkSynthesis {
  [index: string]: object;
}

export interface AreasSynthesis {
  name: string;
  links: LinkSynthesis;
  thermals: string;
  renewables: Array<string>;
  // eslint-disable-next-line camelcase
  filters_synthesis: Array<string>;
  // eslint-disable-next-line camelcase
  filters_year: Array<string>;
}

export interface AreasNameSynthesis {
  [index: string]: AreasSynthesis;
}

export interface StudyProperties {
  archiveInputSeries: Array<string>;
  areas: AreasNameSynthesis;
  bindings: Array<string>;
  enrModelling: string;
  outputPath: string;
  outputs: string;
  path: string;
  sets: string;
  storeNewSet: boolean;
  studyId: string;
  studyPath: string;
  version: number;
}

export interface LinkProperties {
  source: string;
  target: string;
}

export interface AreaLayerColor {
  [key: number]: string;
}
export interface AreaLayerXandY {
  [key: number]: string;
}

export interface AreaUI {
  id: string;
  // eslint-disable-next-line camelcase
  color_b: number;
  // eslint-disable-next-line camelcase
  color_g: number;
  // eslint-disable-next-line camelcase
  color_r: number;
  layers: string;
  x: number;
  y: number;
}

export interface SingleAreaConfig {
  layerColor: AreaLayerColor;
  layerX: AreaLayerXandY;
  layerY: AreaLayerXandY;
  ui: AreaUI;
}

export interface AreasConfig {
  [index: string]: SingleAreaConfig;
}

export interface UpdateAreaUi {
  x: number;
  y: number;
  // eslint-disable-next-line camelcase
  color_rgb: Array<number>;
}

export interface LinkCreationInfo {
  area1: string;
  area2: string;
}

export interface AreaCreationDTO {
  name: string;
  type: object;
  metadata?: object;
  set?: Array<string>;
}

export interface AreaInfoDTO extends AreaCreationDTO {
  id: string;
  thermals: Array<object>;
}

export const isNode = (el: NodeProperties | LinkProperties): boolean =>
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  (el as any).id !== undefined;

export interface TaskView {
  id: string;
  name: ReactNode;
  dateView: ReactNode;
  action: ReactNode;
  date: string;
  type: TaskType;
  status: string;
}

export default {};
