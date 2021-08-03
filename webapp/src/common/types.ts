/* eslint-disable camelcase */
import { Moment } from 'moment';

export type StudyDataType = 'json' | 'file' | 'matrixfile' | 'matrix';

export type StudyPublicMode = "'NONE' | 'READ' | 'EXECUTE' | 'EDIT' | 'FULL'";

export interface StudySummary {
  id: string;
  name: string;
  workspace: string;
}

export interface StudyMetadataOwner {
  id?: number;
  name: string;
}

export interface StudyMetadataDTO {
  owner: StudyMetadataOwner;
  name: string;
  created: number;
  updated: number;
  version: number;
  workspace: string;
  managed: boolean;
  archived: boolean;
  groups: Array<{ id: string; name: string }>;
  public_mode: StudyPublicMode;
}

export interface StudyMetadata {
  id: string;
  name: string;
  creationDate: number;
  modificationDate: number;
  owner: StudyMetadataOwner;
  version: string;
  workspace: string;
  managed: boolean;
  archived: boolean;
  groups: Array<{ id: string; name: string }>;
  publicMode: StudyPublicMode;
}

export type JobStatus =
  | 'JobStatus.RUNNING'
  | 'JobStatus.PENDING'
  | 'JobStatus.SUCCESS'
  | 'JobStatus.FAILED';

export interface LaunchJob {
  id: string;
  studyId: string;
  status: JobStatus;
  creationDate: number;
  completionDate: number;
  msg: string;
  outputId: string;
  exitCode: number;
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

export enum RoleType {
  ADMIN = 40,
  RUNNER = 30,
  WRITER = 20,
  READER = 10,
}

export type IDType = number | string;

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

export enum WSEvent {
  STUDY_CREATED='STUDY_CREATED',
  STUDY_DELETED='STUDY_DELETED',
  STUDY_EDITED='STUDY_EDITED',
  STUDY_JOB_STARTED='STUDY_JOB_STARTED',
  STUDY_JOB_LOG_UPDATE='STUDY_JOB_LOG_UPDATE',
  STUDY_JOB_COMPLETED='STUDY_JOB_COMPLETED',
  STUDY_JOB_STATUS_UPDATE='STUDY_JOB_STATUS_UPDATE'
}

export interface WSMessage {
  type: string;
  payload: unknown;
}

export default {};
