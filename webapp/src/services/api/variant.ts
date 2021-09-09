import client from './client';
import { StudyMetadata, StudyMetadataDTO } from '../../common/types';
import { convertStudyDtoToMetadata } from '../utils';

export const getVariantChildrens = async (id: string): Promise<StudyMetadata[]> => {
  const res = await client.get(`/v1/studies/${id}/variants`);
  return res.data.map((elm: StudyMetadataDTO) => convertStudyDtoToMetadata(elm.id, elm));
};

export const getVariantParents = async (id: string): Promise<StudyMetadata[]> => {
  const res = await client.get(`/v1/studies/${id}/parents`);
  return res.data.map((elm: StudyMetadataDTO) => convertStudyDtoToMetadata(elm.id, elm));
};

export default {};
