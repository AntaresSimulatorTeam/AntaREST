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

export interface UserInfo {
  user: string;
  accessToken: string;
  refreshToken: string;
  expirationDate?: Moment;
}

export default {};
