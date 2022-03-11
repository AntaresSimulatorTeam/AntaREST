import client from './client';

export const getMaintenanceMode = async (): Promise<boolean> => {
  const res = await client.get('/v1/core/maintenance');
  return res.data;
};

export const updateMaintenanceMode = async (data: boolean): Promise<void> => {
  const res = await client.post(`/v1/core/maintenance?maintenance=${data}`);
  return res.data;
};

export const getMessageInfo = async (): Promise<string> => {
  const res = await client.get('/v1/core/maintenance/message');
  return res.data;
};

export const updateMessageInfo = async (data: string): Promise<void> => {
  const res = await client.post('/v1/core/maintenance/message', data);
  return res.data;
};

export default {};
