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
  group_name: string;
  identity_id: number;
  type: RoleType;
}

export interface UserDTO {
  id: number;
  name: string;
}

export interface GroupDTO {
  id: string;
  name: string;
}

export interface UserInfo {
  user: string;
  groups: Array<any>;
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


export default {};