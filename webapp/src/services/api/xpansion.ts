import { XpansionCandidate, XpansionSettings } from '../../components/SingleStudy/XpansionView/types';
import client from './client';

export const createXpansionConfiguration = async (uuid: string): Promise<void> => {
  const res = await client.post(`/v1//studies/${uuid}/extensions/xpansion`);
  return res.data;
};

export const deleteXpansionConfiguration = async (uuid: string): Promise<void> => {
  const res = await client.delete(`/v1/studies/${uuid}/extensions/xpansion`);
  return res.data;
};

export const getXpansionSettings = async (uuid: string): Promise<XpansionSettings> => {
  const res = await client.get(`/v1/studies/${uuid}/extensions/xpansion/settings`);
  return res.data;
};

export const xpansionConfigurationExist = async (uuid: string): Promise<boolean> => {
  try {
    await client.get(`/v1/studies/${uuid}/extensions/xpansion/settings`);
    return Promise.resolve(true);
  } catch (e) {
    const { status } = (e as any).response;
    if (status === 404) {
      return Promise.resolve(false);
    }
    throw e;
  }
};

export const updateXpansionSettings = async (uuid: string, settings: XpansionSettings): Promise<XpansionSettings> => {
  const res = await client.put(`/v1/studies/${uuid}/extensions/xpansion/settings`, settings);
  return res.data;
};

export const getCandidate = async (uuid: string, name: string): Promise<XpansionCandidate> => {
  const res = await client.get(`/v1/studies/${uuid}/extensions/xpansion/candidates/${name}`);
  return res.data;
};

export const getAllCandidates = async (uuid: string): Promise<XpansionCandidate[]> => {
  const res = await client.get(`/v1/studies/${uuid}/extensions/xpansion/candidates`);
  return res.data;
};

export const addCandidate = async (uuid: string, candidate: XpansionCandidate): Promise<XpansionCandidate> => {
  const res = await client.post(`/v1/studies/${uuid}/extensions/xpansion/candidates/add`, candidate);
  return res.data;
};

export const updateCandidate = async (uuid: string, name: string, data: XpansionCandidate): Promise<XpansionCandidate> => {
  const res = await client.put(`/v1/studies/${uuid}/extensions/xpansion/candidates/${name}`, data);
  return res.data;
};

export const deleteCandidate = async (uuid: string, name: string): Promise<XpansionCandidate> => {
  const res = await client.delete(`/v1/studies/${uuid}/extensions/xpansion/candidates/${name}`);
  return res.data;
};

export const getAllConstraints = async (uuid: string): Promise<string[]> => {
  const res = await client.get(`/v1/studies/${uuid}/extensions/xpansion/constraints`);
  return res.data;
};

// update/remove Constraints
// add/update/remove capa

export default {};
