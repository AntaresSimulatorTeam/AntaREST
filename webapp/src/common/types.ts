import { ReactNode } from "react";

export type IdType = number | string;

export interface IdentityDTO<T extends IdType = string> {
  id: T;
  name: string;
}

export type StudyDataType = "json" | "file" | "matrixfile" | "matrix";

export type StudyPublicMode = "NONE" | "READ" | "EXECUTE" | "EDIT" | "FULL";

export interface GenericInfo {
  id: IdType;
  name: string;
}

export interface StudySummary {
  id: string;
  name: string;
  workspace: string;
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
  groups: Array<IdentityDTO>;
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
  name?: string;
  author?: string;
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
  archived: boolean;
}

export interface StudyLayer {
  areas: string[];
  id: string;
  name: string;
}

export interface VariantTreeDTO {
  node: StudyMetadataDTO;
  children: Array<VariantTreeDTO>;
}

export interface VariantTree {
  node: StudyMetadata;
  children: Array<VariantTree>;
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
  // eslint-disable-next-line camelcase
  xpansion_r_version?: boolean;
  // eslint-disable-next-line camelcase
  nb_cpu?: number;
  // eslint-disable-next-line camelcase
  time_limit?: number;
  // eslint-disable-next-line camelcase
  post_processing?: boolean;
  // eslint-disable-next-line camelcase
  adequacy_patch?: AdequacyPatchParams;
  // eslint-disable-next-line camelcase
  output_suffix?: string;
  // eslint-disable-next-line camelcase
  other_options?: string;
  // eslint-disable-next-line camelcase
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

export interface LaunchJobsProgress {
  [key: string]: number;
}

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
  roles: Array<RoleDTO>;
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
  groups: Array<JWTGroup>;
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
  roles: Array<RoleDTO>;
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

export interface UserToken {
  user: UserDTO;
  bots: Array<BotDTO>;
}

export interface MatrixType {
  columns: Array<string>;
  index: Array<string | number>;
  data: Array<Array<number>>;
}

export type MatrixInfoDTO = IdentityDTO;

export interface MatrixDataSetDTO extends IdentityDTO {
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
  id: string;
  width: number;
  height: number;
  index: Array<string>;
  columns: Array<string>;
  data: Array<Array<number>>;
  created_at: number;
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
  STUDY_DATA_EDITED = "STUDY_DATA_EDITED",
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
  LAUNCH_PROGRESS = "LAUNCH_PROGRESS",
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
export interface WSMessage<T = any> {
  type: string;
  payload: T;
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
  UPGRADE_STUDY = "UPGRADE_STUDY",
  UNKNOWN = "UNKNOWN",
}

export interface TaskDTO extends IdentityDTO<string> {
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
  item_list: Array<LinkClusterElement>;
}

export interface AllClustersAndLinks {
  links: Array<LinkClusterItem>;
  clusters: Array<LinkClusterItem>;
}

export type LinkListElement = { [elm: string]: LinkElement };

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
  data: {
    [id: string]: {
      [elm: string]: {
        [item: string]: Array<number>;
      };
    };
  };
  warnings: Array<string>;
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

export interface LinkProperties {
  source: string;
  target: string;
  temp?: boolean;
}

export interface AreaLayerColor {
  [key: string]: string;
}
export interface AreaLayerPosition {
  [key: string]: number;
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
  layerX: AreaLayerPosition;
  layerY: AreaLayerPosition;
  ui: AreaUI;
}

export interface AreasConfig {
  [areaId: string]: SingleAreaConfig;
}

export interface UpdateAreaUi {
  x: number;
  y: number;
  // eslint-disable-next-line camelcase
  color_rgb: Array<number>;
  layerX: AreaLayerPosition;
  layerY: AreaLayerPosition;
  layerColor: AreaLayerColor;
}

export interface LinkUIInfoDTO {
  color: string;
  style: string;
  width: number;
}

export interface LinkCreationInfoDTO {
  area1: string;
  area2: string;
}

export interface LinkInfoWithUI extends LinkCreationInfoDTO {
  ui: LinkUIInfoDTO;
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

export interface TaskView {
  id: string;
  name: ReactNode;
  dateView: ReactNode;
  action: ReactNode;
  date: string;
  type: TaskType;
  status: string;
}

export interface ThematicTrimmingConfigDTO {
  "OV. COST": boolean;
  "OP. COST": boolean;
  "MRG. PRICE": boolean;
  "CO2 EMIS.": boolean;
  "DTG by plant": boolean;
  BALANCE: boolean;
  "ROW BAL.": boolean;
  PSP: boolean;
  "MISC. NDG": boolean;
  LOAD: boolean;
  "H. ROR": boolean;
  WIND: boolean;
  SOLAR: boolean;
  NUCLEAR: boolean;
  LIGNITE: boolean;
  COAL: boolean;
  GAS: boolean;
  OIL: boolean;
  "MIX. FUEL": boolean;
  "MISC. DTG": boolean;
  "H. STOR": boolean;
  "H. PUMP": boolean;
  "H. LEV": boolean;
  "H. INFL": boolean;
  "H. OVFL": boolean;
  "H. VAL": boolean;
  "H. COST": boolean;
  "UNSP. ENRG": boolean;
  "SPIL. ENRG": boolean;
  LOLD: boolean;
  LOLP: boolean;
  "AVL DTG": boolean;
  "DTG MRG": boolean;
  "MAX MRG": boolean;
  "NP COST": boolean;
  "NP Cost by plant": boolean;
  NODU: boolean;
  "NODU by plant": boolean;
  "FLOW LIN.": boolean;
  "UCAP LIN.": boolean;
  "LOOP FLOW": boolean;
  "FLOW QUAD.": boolean;
  "CONG. FEE (ALG.)": boolean;
  "CONG. FEE (ABS.)": boolean;
  "MARG. COST": boolean;
  "CONG. PROD +": boolean;
  "CONG. PROD -": boolean;
  "HURDLE COST": boolean;
  // Study version >= 810
  "RES generation by plant"?: boolean;
  "MISC. DTG 2"?: boolean;
  "MISC. DTG 3"?: boolean;
  "MISC. DTG 4"?: boolean;
  "WIND OFFSHORE"?: boolean;
  "WIND ONSHORE"?: boolean;
  "SOLAR CONCRT."?: boolean;
  "SOLAR PV"?: boolean;
  "SOLAR ROOFT"?: boolean;
  "RENW. 1"?: boolean;
  "RENW. 2"?: boolean;
  "RENW. 3"?: boolean;
  "RENW. 4"?: boolean;
}
