import { getConfig } from '../config';
import client from './client';

export interface FileDownloadDTO {
  id: string;
  name: string;
  filename: string;
  // eslint-disable-next-line camelcase
  expiration_date: string;
  ready: boolean;
  failed: boolean;
  // eslint-disable-next-line camelcase
  error_message: string;
}

export interface FileDownload {
  id: string;
  name: string;
  filename: string;
  expirationDate: string;
  ready: boolean;
  failed: boolean;
  errorMessage: string;
}

export interface FileDownloadTask {
  file: FileDownloadDTO;
  task: string;
}

export const convertFileDownloadDTO = (fileDownload: FileDownloadDTO): FileDownload => ({
  id: fileDownload.id,
  name: fileDownload.name,
  filename: fileDownload.filename,
  expirationDate: fileDownload.expiration_date,
  ready: fileDownload.ready,
  failed: fileDownload.failed,
  errorMessage: fileDownload.error_message,
});

export const getDownloadsList = async (): Promise<Array<FileDownload>> => {
  const res = await client.get('/v1/downloads');
  return res.data.map(convertFileDownloadDTO);
};

export const getDownloadUrl = (did: string): string =>
  `${getConfig().downloadHostUrl || (getConfig().baseUrl + getConfig().restEndpoint)}/v1/downloads/${did}`;
