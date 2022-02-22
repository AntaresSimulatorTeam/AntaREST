import client from './client';
import { CommandDTO, StudyMetadata, StudyMetadataDTO, TaskDTO, VariantTree } from '../../common/types';
import { convertStudyDtoToMetadata, convertVariantTreeDTO } from '../utils';

export const getVariantChildren = async (id: string): Promise<VariantTree> => {
  const res = await client.get(`/v1/studies/${id}/variants`);
  return convertVariantTreeDTO(res.data);
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

export const appendCommand = async (studyId: string, command: CommandDTO): Promise<string> => {
  const res = await client.post(`/v1/studies/${studyId}/command`, command);
  return res.data;
};

export const moveCommand = async (studyId: string, commandId: string, index: number): Promise<any> => {
  const res = await client.put(`/v1/studies/${studyId}/commands/${commandId}/move?index=${encodeURIComponent(index)}`);
  return res.data;
};

export const updateCommand = async (studyId: string, commandId: string, command: CommandDTO): Promise<any> => {
  const res = await client.put(`/v1/studies/${studyId}/commands/${commandId}`, command);
  return res.data;
};

export const replaceCommands = async (studyId: string, commands: Array<CommandDTO>): Promise<string> => {
  const res = await client.put(`/v1/studies/${studyId}/commands`, commands);
  return res.data;
};

export const deleteCommand = async (studyId: string, commandId: string): Promise<any> => {
  const res = await client.delete(`/v1/studies/${studyId}/commands/${commandId}`);
  return res.data;
};

export const deleteAllCommands = async (studyId: string): Promise<any> => {
  const res = await client.delete(`/v1/studies/${studyId}/commands`);
  return res.data;
};

export const getCommand = async (studyId: string, commandId: string): Promise<CommandDTO> => {
  const res = await client.get(`/v1/studies/${studyId}/commands/${commandId}`);
  return res.data;
};

export const getCommands = async (studyId: string): Promise<Array<CommandDTO>> => {
  const res = await client.get(`/v1/studies/${studyId}/commands`);
  return res.data;
};

export const applyCommands = async (studyId: string, denormalize = false): Promise<string> => {
  const res = await client.put(`/v1/studies/${studyId}/generate?denormalize=${denormalize}&from_scratch=true`);
  return res.data;
};

export const getStudyTask = async (studyId: string): Promise<TaskDTO> => {
  const res = await client.get(`/v1/studies/${studyId}/task`);
  return res.data;
};

export default {};
