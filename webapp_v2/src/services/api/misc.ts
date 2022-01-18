import client from './client';

export interface APIVersion {
  version: string;
  gitcommit: string;
}

export const getVersion = async (): Promise<APIVersion> => {
  const res = await client.get('/version');
  return res.data;
};

export default {};
