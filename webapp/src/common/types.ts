import { Moment } from 'moment';

export interface StudyMetadataDTO {
  author: string;
  caption: string;
  created: number;
  lastsave: number;
  version: number;
}

export interface StudyListDTO {
  antares: StudyMetadataDTO;
}

export interface StudyMetadata {
  id: string;
  name: string;
  creationDate: number;
  modificationDate: number;
  author: string;
  version: string;
}

export enum RoleType {
  ADMIN = 40,
  RUNNER = 30,
  WRITER =  20,
  READER = 10
}

export type IDType = number | string;

export interface RoleDTO {
  group_id: string;
  user: number;
  type: RoleType;
}

export interface UserDTO {
  id: number;
  name: string;
}

export interface UserRoleDTO {
  id: string;
  name: string;
  role: RoleType;
}

export interface UserInfosDTO {
  id: number;
  name: string;
  roles: Array<UserRoleDTO>
}


export interface GroupDTO {
  id: string;
  name: string;
}

export interface UserInfo {
  user: string;
  groups: Array<UserRoleDTO>;
  id: number;
  impersonator: number;
  type: string;
  accessToken: string;
  refreshToken: string;
  expirationDate?: Moment;
}

export interface TokenDTO {
  id: number;
  name: string;
  owner: number;
  isAuthor: boolean;
}

export interface BotDTO {
  name: string;
  is_author: boolean;
}

export interface BotRoleUpdateDTO {
  id: number;
  name: string;
  is_author: boolean;
}


export default {};
