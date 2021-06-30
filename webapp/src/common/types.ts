/* eslint-disable camelcase */
import { Moment } from 'moment';

export type StudyDataType = 'json' | 'file' | 'matrix';

export interface StudyMetadataDTO {
  author: string;
  name: string;
  created: number;
  updated: number;
  version: number;
}

export interface StudyMetadata {
  id: string;
  name: string;
  creationDate: number;
  modificationDate: number;
  author: string;
  version: string;
}

export type JobStatus = 'JobStatus.RUNNING' | 'JobStatus.PENDING' | 'JobStatus.SUCCESS' | 'JobStatus.FAILED';

export interface LaunchJob {
  id: string;
  studyId: string;
  status: JobStatus;
  creationDate: number;
  completionDate: number;
  msg: string;
  exitCode: number;
}

export enum RoleType {
  ADMIN = 40,
  RUNNER = 30,
  WRITER = 20,
  READER = 10
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

export interface BotCreateDTO{
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

export default {};
