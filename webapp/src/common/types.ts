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

export interface UserDTO {
  id: number;
  name: string;
}

export type RoleType = 40 | 30 | 20 | 10;

export interface RoleDTO {
  group_id: string;
  user: number;
  type: RoleType;
}

export interface UserGroupInfo {
  id: number;
  name: string;
  role: RoleType;
}

export interface GroupDTO {
  id: string;
  name: string;
}

export interface UserInfo {
  user: string;
  accessToken: string;
  refreshToken: string;
  expirationDate?: Moment;
}

export default {};
