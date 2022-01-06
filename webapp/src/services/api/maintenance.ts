import { MaintenanceDTO } from '../../common/types';
import client from './client';

export const getMaintenanceMode = async (): Promise<MaintenanceDTO> => {
  const res = await client.get('/v1/core/maintenance');
  return res.data;
};

export const updateMaintenanceMode = async (data: MaintenanceDTO): Promise<MaintenanceDTO> => {
  const res = await client.post('/v1/core/maintenance', data);
  return res.data;
};

export default {};
