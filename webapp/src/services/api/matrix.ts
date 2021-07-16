import { AxiosRequestConfig } from 'axios';
import client from './client';
import { MatrixDTO, MatrixDataSetDTO, MatrixInfoDTO, MatrixDataSetUpdateDTO } from '../../common/types';

export const getMatrixList = async (name: string = "", filter_own: boolean = false): Promise<Array<MatrixDataSetDTO>> => {
  const res = await client.get(`/v1/matrixdataset/_search?name=${encodeURI(name)}&filter_own=${filter_own}`);
  return res.data;
};

export const getMatrix = async (id: string): Promise<MatrixDTO> => {
  const res = await client.get(`/v1//matrix/${id}`);
  return res.data;
};

export const createMatrixByImportation = async (file: File, onProgress?: (progress: number) => void): Promise<Array<MatrixInfoDTO>> => {
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
  const res = await client.post('/v1/matrix/_import', formData, restconfig);
  return res.data;
};

export const createDataSet = async (metadata: MatrixDataSetUpdateDTO, matrices: Array<MatrixInfoDTO>): Promise<MatrixDataSetDTO> => {
  const data = { metadata, matrices };
  const res = await client.post('/v1/matrixdataset', data);
  return res.data;
};

export const updateDataSet = async (id: string, metadata: MatrixDataSetUpdateDTO): Promise<MatrixDataSetUpdateDTO> => {
  console.log('UPDATE: ', metadata);
  const res = await client.put(`/v1/matrixdataset/${id}/metadata`, metadata);
  return res.data;
};

export default {};
