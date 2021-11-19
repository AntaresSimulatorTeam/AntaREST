import { AxiosRequestConfig } from 'axios';
import client from './client';
import { LaunchJob, StudyMetadata, StudyMetadataDTO, StudyOutput, StudyPublicMode } from '../../common/types';
import { getConfig } from '../config';
import { convertStudyDtoToMetadata } from '../utils';

const getStudiesRaw = async (): Promise<{[sid: string]: StudyMetadataDTO}> => {
  const res = await client.get('/v1/studies?summary=true');
  return res.data;
};

export const getStudies = async (): Promise<StudyMetadata[]> => {
  const rawStudyList = await getStudiesRaw();
  return Object.keys(rawStudyList).map((sid) => {
    const study = rawStudyList[sid];
    return convertStudyDtoToMetadata(sid, study);
  });
};

export const getStudyData = async (sid: string, path = '', depth = 1): Promise<any> => {
  const res = await client.get(`/v1/studies/${sid}/raw?path=${encodeURIComponent(path)}&depth=${depth}`);
  return res.data;
};

export const getComments = async (sid: string): Promise<any> => {
  const res = await client.get(`/v1/studies/${sid}/comments`);
  return res.data;
};

export const getStudyMetadata = async (sid: string, summary = true): Promise<StudyMetadata> => {
  const res = await client.get(`/v1/studies/${sid}?summary=${summary}`);
  return convertStudyDtoToMetadata(sid, res.data);
};

export const getStudyOutputs = async (sid: string): Promise<Array<StudyOutput>> => {
  const res = await client.get(`/v1/studies/${sid}/outputs`);
  return res.data;
};

export const createStudy = async (name: string, version: number): Promise<string> => {
  const res = await client.post(`/v1/studies?name=${encodeURIComponent(name)}&version=${version}`);
  return res.data;
};

export const editStudy = async (data: object, sid: string, path = '', depth = 1): Promise<any> => {
  const res = await client.post(`/v1/studies/${sid}/raw?path=${encodeURIComponent(path)}&depth=${depth}`, data);
  return res.data;
};

export const copyStudy = async (sid: string, name: string, withOutputs = false): Promise<any> => {
  const res = await client.post(`/v1/studies/${sid}/copy?dest=${encodeURIComponent(name)}&with_outputs=${withOutputs}`);
  return res.data;
};

export const archiveStudy = async (sid: string): Promise<void> => {
  await client.put(`/v1/studies/${sid}/archive`);
};

export const unarchiveStudy = async (sid: string): Promise<void> => {
  await client.put(`/v1/studies/${sid}/unarchive`);
};

export const deleteStudy = async (sid: string): Promise<any> => {
  const res = await client.delete(`/v1/studies/${sid}`);
  return res.data;
};

export const editComments = async (sid: string, newComments: string): Promise<any> => {
  const data = { comments: newComments };
  const res = await client.put(`/v1/studies/${sid}/comments`, data);
  return res.data;
};

export const getExportUrl = (sid: string, skipOutputs = false): string =>
  `${getConfig().downloadHostUrl || (getConfig().baseUrl + getConfig().restEndpoint)}/v1/studies/${sid}/export?no_output=${skipOutputs}`;

export const exportOuput = async (sid: string, output: string): Promise<void> => {
  const res = await client.post(`/v1/studies/${sid}/outputs/${output}/download`, undefined, { responseType: 'blob' });
  const url = window.URL.createObjectURL(new Blob([await res.data]));
  const link = document.createElement('a');
  link.href = url;
  link.setAttribute('download', `${output}.zip`);
  document.body.appendChild(link);
  link.click();
};

export const importStudy = async (file: File, onProgress?: (progress: number) => void): Promise<string> => {
  const options: AxiosRequestConfig = {};
  if (onProgress) {
    options.onUploadProgress = (progressEvent): void => {
      const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
      onProgress(percentCompleted);
    };
  }
  const formData = new FormData();
  formData.append('study', file);
  const restconfig = {
    ...options,
    headers: {
      'content-type': 'multipart/form-data',
      'Access-Control-Allow-Origin': '*',
    },
  };
  const res = await client.post('/v1/studies/_import', formData, restconfig);
  return res.data;
};

export const importFile = async (file: File, study: string, path: string, onProgress?: (progress: number) => void): Promise<string> => {
  const options: AxiosRequestConfig = {};
  if (onProgress) {
    options.onUploadProgress = (progressEvent): void => {
      const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
      onProgress(percentCompleted);
    };
  }
  const formData = new FormData();
  formData.append('file', file);
  const restconfig = {
    ...options,
    headers: {
      'content-type': 'multipart/form-data',
      'Access-Control-Allow-Origin': '*',
    },
  };
  const res = await client.put(`/v1/studies/${study}/raw?path=${encodeURIComponent(path)}`, formData, restconfig);
  return res.data;
};

export const launchStudy = async (sid: string): Promise<string> => {
  const res = await client.post(`/v1/launcher/run/${sid}`);
  return res.data;
};

export const killStudy = async (jid: string): Promise<string> => {
  const res = await client.post(`/v1/launcher/jobs/${jid}/kill`);
  return res.data;
};

export const mapLaunchJobDTO = (j: any): LaunchJob => ({
  id: j.id,
  studyId: j.study_id,
  status: j.status,
  creationDate: j.creation_date,
  completionDate: j.completion_date,
  msg: j.msg,
  outputId: j.output_id,
  exitCode: j.exit_code,
});

export const getStudyJobs = async (sid?: string): Promise<LaunchJob[]> => {
  const query = sid ? `?study=${sid}` : '';
  const res = await client.get(`/v1/launcher/jobs${query}`);
  const data = await res.data;
  return data.map(mapLaunchJobDTO);
};

export const getStudyJobLog = async (jid: string, logType = 'STDOUT'): Promise<string|undefined> => {
  const res = await client.get(`/v1/launcher/jobs/${jid}/logs?log_type=${logType}`);
  return res.data;
};

export const changeStudyOwner = async (studyId: string, newOwner: number): Promise<string|undefined> => {
  const res = await client.put(`/v1/studies/${studyId}/owner/${newOwner}`);
  return res.data;
};

export const deleteStudyGroup = async (studyId: string, groupId: string): Promise<any> => {
  const res = await client.delete(`/v1/studies/${studyId}/groups/${groupId}`);
  return res.data;
};

export const addStudyGroup = async (studyId: string, groupId: string): Promise<any> => {
  const res = await client.put(`/v1/studies/${studyId}/groups/${groupId}`);
  return res.data;
};

export const changePublicMode = async (studyId: string, publicMode: StudyPublicMode): Promise<string|undefined> => {
  const res = await client.put(`/v1/studies/${studyId}/public_mode/${publicMode}`);
  return res.data;
};

export const renameStudy = async (studyId: string, name: string): Promise<any> => {
  const res = await client.put(`/v1/studies/${studyId}`, {
    name,
  });
  return res.data;
};

export default {};
