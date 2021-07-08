import { AxiosRequestConfig } from 'axios';
import client from './client';
import { MatrixDTO, MatrixUserMetadataQuery, MatrixMetadataDTO } from '../../common/types';

export const getMatrixList = async (query: MatrixUserMetadataQuery): Promise<Array<MatrixMetadataDTO>> => {
  const res = await client.post('/v1//matrix/_search', query);
  return res.data;
};

export const getMatrix = async (id: string): Promise<MatrixDTO> => {
  const res = await client.get(`/v1//matrix/${id}`);
  return res.data;
};

export const createMatrix = async (matrix: MatrixDTO): Promise<string> => {
  const res = await client.post('/v1/matrix', matrix);
  return res.data;
};

export const createMatrixByImportation = async (file: File, onProgress?: (progress: number) => void): Promise<string> => {
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

function parameterizeArray(key: string, arr: Array<string>): string {
  const newArr = arr.map(encodeURIComponent);
  return `&${key}=${newArr.join(`&${key}=`)}`;
}

export const updateMetadata = async (metadata: MatrixMetadataDTO): Promise<MatrixMetadataDTO> => {
  const name = encodeURIComponent(metadata.name);
  const publicStatus = encodeURIComponent(metadata.public);
  const { length } = metadata.groups;
  let groupUrl = '&';
  if (length > 0) {
    groupUrl = `${parameterizeArray('groups', metadata.groups.map((elm) => encodeURIComponent(elm.id)))}&`;
  }
  const res = await client.put(`v1/matrix/${metadata.id}/metadata?name=${name}${groupUrl}public=${publicStatus}`, metadata.metadata);
  return res.data;
};

export default {};
