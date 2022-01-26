import { UpdateAreaUi } from '../../components/SingleStudy/MapView/types';
import client from './client';

export const createArea = async (uuid: string, name: string): Promise<string> => {
  const res = await client.post(`/v1/studies/${uuid}/areas?uuid=${uuid}`, { name, type: 'AREA' });
  return res.data;
};

export const createLink = async (uuid: string): Promise<string> => {
  const res = await client.post(`/v1/studies/${uuid}/links`);
  return res.data;
};

export const updateAreaUI = async (uuid: string, areaId: string, areaUi: UpdateAreaUi): Promise<string> => {
  const res = await client.put(`/v1/studies/${uuid}/areas/${areaId}/ui?uuid=${uuid}&area_id=${areaId}`, areaUi);
  return res.data;
};

export const deleteArea = async (uuid: string, areaId: string): Promise<string> => {
  const res = await client.delete(`/v1/studies/${uuid}/areas/${areaId}`);
  return res.data;
};

export const deleteLink = async (uuid: string, areaIdFrom: string, areaIdTo: string): Promise<string> => {
  const res = await client.delete(`/v1/studies/${uuid}/links/${areaIdFrom}/${areaIdTo}`);
  return res.data;
};

export default {};
