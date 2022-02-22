import { XpansionCandidate, XpansionSettings } from '../../components/SingleStudy/XpansionView/types';
import client from './client';

export const createXpansion = async (uuid: string, name: string): Promise<XpansionCandidate> => {
  const res = await client.post(`/v1/studies/${uuid}/extensions/xpansion/create?`);
  return res.data;
};

export const deleteXpansion = async (uuid: string, name: string): Promise<XpansionCandidate> => {
  const res = await client.post(`/v1/studies/${uuid}/extensions/xpansion/delete?`);
  return res.data;
};

export const getXpansionSettings = async (uuid: string): Promise<XpansionSettings> => {
  const res = await client.get(`/v1/studies/${uuid}/extensions/xpansion/settings?${uuid}`);
  return res.data;
};

export const updateXpansionSettings = async (uuid: string, name: string): Promise<XpansionSettings> => {
  const res = await client.post(`/v1/studies/${uuid}/extensions/xpansion/settings?`);
  return res.data;
};

export const getCandidate = async (uuid: string, name: string): Promise<XpansionCandidate> => {
  const res = await client.get(`/v1/studies/${uuid}/extensions/xpansion/candidates/${name}`);
  return res.data;
};

export const getAllCandidates = async (uuid: string): Promise<XpansionCandidate> => {
  const res = await client.get(`/v1/studies/${uuid}/extensions/xpansion/candidates/`);
  return res.data;
};

export const addCandidate = async (uuid: string, name: string): Promise<XpansionCandidate> => {
  const res = await client.post(`/v1/studies/${uuid}/extensions/xpansion/candidate/add?`);
  return res.data;
};

export const updateCandidate = async (uuid: string, name: string): Promise<XpansionCandidate> => {
  const res = await client.post(`/v1/studies/${uuid}/extensions/xpansion/`);
  return res.data;
};

export const deleteCandidate = async (uuid: string, name: string): Promise<XpansionCandidate> => {
  const res = await client.post(`/v1/studies/${uuid}/extensions/xpansion/`);
  return res.data;
};

// update/remove Constraints
// add/update/remove capa

export default {};
