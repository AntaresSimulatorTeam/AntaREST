import { StudyMetadata } from '../../common/types';

export type StudyTreeLeaf = StudyMetadata;
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
  const tree: StudyTreeNode = { name: '', child: [] };
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
  console.log('TREE MF: ', tree);
  return tree;
};
