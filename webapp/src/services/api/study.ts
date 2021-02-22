import { AxiosRequestConfig } from 'axios';
import client from './client';
import { StudyMetadata, StudyListDTO } from '../../common/types';
import { getConfig } from '../config';
import { convertStudyDtoToMetadata } from '../utils';


const getStudiesRaw = async (): Promise<{[sid: string]: StudyListDTO}> => {
  const res = await client.get('/studies');
  return res.data;
};

export const getStudies = async (): Promise<StudyMetadata[]> => {
  const rawStudyList = await getStudiesRaw();
  return Object.keys(rawStudyList).map((sid) => {
    const study = rawStudyList[sid];
    return convertStudyDtoToMetadata(sid, study.antares);
  });
};

export const getStudyData = async (sid: string, path = '', depth = 1): Promise<any> => {
  const res = await client.get(`/studies/${sid}/${path}?depth=${depth}`);
  return res.data;
};

export const createStudy = async (name: string): Promise<string> => {
  const res = await client.post(`/studies/${name}`);
  return res.data;
};

export const deleteStudy = async (sid: string): Promise<any> => {
  const res = await client.delete(`/studies/${sid}`);
  return res.data;
};

export const getExportUrl = (sid: string, compact = false, skipOutputs = false): string =>
  `${getConfig().downloadHostUrl || (getConfig().baseUrl + getConfig().restEndpoint)}/studies/${sid}/export?compact=${compact}&skipOutputs=${skipOutputs}`;

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
  const res = await client.post('/studies', formData, restconfig);
  return res.data;
};

export default {};
