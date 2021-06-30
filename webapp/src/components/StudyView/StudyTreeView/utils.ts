import { StudyDataType } from '../../../common/types';

export interface StudyParams {
  type: StudyDataType;
  icon: 'file-alt' | 'file-code';
  data: string | {path: string; json: string};
}

export const isJsonLeaf = (studyDataNode: any) => {
  // this is a non robust guess work
  const childrenKeys = Object.keys(studyDataNode);
  for (let index = 0; index < childrenKeys.length; index += 1) {
    const element = studyDataNode[childrenKeys[index]];
    // here if one the child of the current node is not an object (so it's a string or an array) and this string is not a file
    // this means this object is like {"a": "something"} or {"a": ["b","c"]}
    // BUT it could be something like {"a": "something", "b": {"c": "file://xxx"}}} so a kind of hybrid between a folder and a leaf node
    // though I guess this is not possible but i'm not sure...
    // the idea is that if all children is an object or a "file://", it is to be considered a folder
    if (
      typeof element !== 'object' &&
      (typeof element !== 'string' ||
        !(element.includes('file://') || element.includes('matrix://') || element.includes('matrixfile://')))
    ) {
      return true;
    }
  }
  return false;
};

export const getStudyParams = (
  data: any,
  path: string,
  itemkey: string,
): StudyParams | undefined => {
  if (typeof data !== 'object') {
    const tmp = data.split('://');
    if (tmp && tmp.length > 0) {
      return { type: tmp[0] as StudyDataType, icon: 'file-alt', data: `${path}/${itemkey}` };
    }
    return { type: 'file', icon: 'file-alt', data: `${path}/${itemkey}` };
  }
  if (isJsonLeaf(data)) {
    return { type: 'json', icon: 'file-code', data: { path: `${path}/${itemkey}`, json: JSON.stringify(data) } };
  }
  return undefined;
};

export default {};
