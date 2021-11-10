/* eslint-disable no-plusplus */
import { StudyMetadata } from '../../common/types';

export interface StudyTreeNode {
    name: string;
    child: Array<StudyTreeNode | StudyMetadata>;
  }

const nodeProcess = (tree: StudyTreeNode, path: Array<string>, study: StudyMetadata): void => {
  const { child } = tree;
  const { length } = path;
  if (length === 1) {
    child.push(study);
    return;
  }
  const element = path[length - 1];
  const index = child.findIndex((elm: StudyTreeNode | StudyMetadata) => elm.name === element);
  if (index < 0) {
    path.pop();
    child.push({ name: element, child: [] });
    nodeProcess(child[child.length - 1] as StudyTreeNode, path, study);
  } else {
    path.pop();
    nodeProcess(child[index] as StudyTreeNode, path, study);
  }
};

export const buildStudyTree = (studies: Array<StudyMetadata>): StudyTreeNode => {
  const tree: StudyTreeNode = { name: 'root', child: [] };
  let path: Array<string> = [];
  for (let i = 0; i < studies.length; i++) {
    if (studies[i].folder !== undefined && studies[i].folder !== null) {
      path = [studies[i].workspace, ...(studies[i].folder as string).split('/').filter((elm) => elm !== '')];
    } else {
      path = [studies[i].workspace];
    }
    path.reverse();
    nodeProcess(tree, path, studies[i]);
  }
  return tree;
};

export const isDir = (element: StudyTreeNode | StudyMetadata): boolean => (element as StudyMetadata).id === undefined;

export interface FindNodeResult {
  path: Array<string>;
  node: StudyTreeNode | undefined;
}

export const findNode = (name: string, element: StudyTreeNode, path: Array<string> = []): FindNodeResult => {
  if (element.name === name) return { node: element, path: path.concat([element.name]) };

  let result: FindNodeResult = {
    path: [],
    node: undefined,
  };
  for (let i = 0; i < element.child.length; i++) {
    if (isDir(element.child[i])) {
      result = findNode(name, element.child[i] as StudyTreeNode, path.concat([element.name]));
      if (result.node !== undefined) {
        break;
      }
    }
  }
  return result;
};

export default {};
