import client from './client';
import { CommandDTO, StudyMetadata, StudyMetadataDTO } from '../../common/types';
import { convertStudyDtoToMetadata } from '../utils';

export const getVariantChildrens = async (id: string): Promise<StudyMetadata[]> => {
  const res = await client.get(`/v1/studies/${id}/variants`);
  return res.data.map((elm: StudyMetadataDTO) => convertStudyDtoToMetadata(elm.id, elm));
};

export const getVariantParents = async (id: string): Promise<StudyMetadata[]> => {
  const res = await client.get(`/v1/studies/${id}/parents`);
  return res.data.map((elm: StudyMetadataDTO) => convertStudyDtoToMetadata(elm.id, elm));
};

export const createVariant = async (id: string, name: string): Promise<string> => {
  const res = await client.post(`/v1/studies/${id}/variants?name=${encodeURIComponent(name)}`);
  return res.data;
};

export const appendCommands = async (studyId: string, commands: Array<CommandDTO>): Promise<string> => {
  const res = await client.post(`/v1/studies/${studyId}/commands`, commands);
  return res.data;
};

export const getCommands = async (studyId: string): Promise<Array<CommandDTO>> => {
  const res = await client.get(`/v1/studies/${studyId}/commands`);
  return res.data;
};

export default {};
