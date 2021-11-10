/* eslint-disable no-plusplus */
import { StudyMetadata } from '../../common/types';

export interface StudyTreeNode {
    name: string;
    children: Array<StudyTreeNode | StudyMetadata>;
  }

export const isDir = (element: StudyTreeNode | StudyMetadata): boolean => (element as StudyMetadata).id === undefined;

const nodeProcess = (tree: StudyTreeNode, path: Array<string>, study: StudyMetadata): void => {
  const { children } = tree;
  if (path.length === 1) {
    children.push(study);
    return;
  }

  const element = path.pop() || '';
  const index = children.findIndex((elm: StudyTreeNode | StudyMetadata) => isDir(elm) && elm.name === element);
  if (index < 0) {
    children.push({ name: element, children: [] });
    nodeProcess(children[children.length - 1] as StudyTreeNode, path, study);
  } else {
    nodeProcess(children[index] as StudyTreeNode, path, study);
  }
};

export const buildStudyTree = (studies: Array<StudyMetadata>): StudyTreeNode => {
  const tree: StudyTreeNode = { name: 'root', children: [] };
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
  for (let i = 0; i < element.children.length; i++) {
    if (isDir(element.children[i])) {
      result = findNode(name, element.children[i] as StudyTreeNode, path.concat([element.name]));
      if (result.node !== undefined) {
        break;
      }
    }
  }
  return result;
};

export default {};
