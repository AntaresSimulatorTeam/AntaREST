import client from './client';
import { MatrixDTO, MatrixUserMetadataQuery, MatrixMetadataDTO } from '../../common/types';

export const getMatrixList = async (query: MatrixUserMetadataQuery): Promise<Array<MatrixMetadataDTO>> => {
  const res = await client.post(`/v1//matrix/_search`, query);
  return res.data;
};

export const getMatrix = async (id: string): Promise<MatrixDTO> => {
    const res = await client.get(`/v1//matrix/${id}`);
    return res.data;
  };

export const createMatrix = async (matrix: MatrixDTO): Promise<string> => {
  const res = await client.post(`/v1/matrix`, matrix);
  return res.data;
};


export default {};
