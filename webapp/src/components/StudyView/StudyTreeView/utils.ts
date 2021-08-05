import { StudyDataType } from '../../../common/types';

export interface StudyParams {
  type: StudyDataType;
  icon: 'file-alt' | 'file-code';
  data: string;
}

export const getStudyParams = (
  data: any,
  path: string,
  itemkey: string,
): StudyParams | undefined => {
  if (typeof data !== 'object') {
    const tmp = data.split('://');
    if (tmp && tmp.length > 0) {
      if (tmp[0] === 'json') {
        return { type: 'json', icon: 'file-code', data: `${path}/${itemkey}` };
      }
      return { type: tmp[0] as StudyDataType, icon: 'file-alt', data: `${path}/${itemkey}` };
    }
    return { type: 'file', icon: 'file-alt', data: `${path}/${itemkey}` };
  }
  return undefined;
};

export default {};
