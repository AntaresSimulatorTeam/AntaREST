import { FileDownload } from '../../common/types';
import { getConfig } from '../config';
import client from './client';

export const getDownloadsList = async (): Promise<Array<FileDownload>> => {
  const res = await client.get('/v1/downloads');
  return res.data.map((d: any) => ({
    id: d.id,
    name: d.name,
    filename: d.filename,
    expirationData: d.expiration_date,
    ready: d.ready,
  }));
};

export const getDownloadUrl = (did: string): string =>
  `${getConfig().downloadHostUrl || (getConfig().baseUrl + getConfig().restEndpoint)}/v1/downloads/${did}`;
