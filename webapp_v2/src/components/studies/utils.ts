/* eslint-disable no-plusplus */
import { StudyMetadata } from "../../common/types";

export interface StudyTreeNode {
  name: string;
  children: Array<StudyTreeNode>;
}

const nodeProcess = (tree: StudyTreeNode, path: Array<string>): void => {
  const { children } = tree;
  if (path.length === 1) {
    return;
  }
  const element = path.pop() || "";
  const index = children.findIndex(
    (elm: StudyTreeNode) => elm.name === element
  );
  if (index < 0) {
    children.push({ name: element, children: [] });
    nodeProcess(children[children.length - 1] as StudyTreeNode, path);
  } else {
    nodeProcess(children[index] as StudyTreeNode, path);
  }
};

export const buildStudyTree = (
  studies: Array<StudyMetadata>
): StudyTreeNode => {
  const tree: StudyTreeNode = { name: "root", children: [] };
  let path: Array<string> = [];
  for (let i = 0; i < studies.length; i++) {
    if (studies[i].folder !== undefined && studies[i].folder !== null) {
      path = [
        studies[i].workspace,
        ...(studies[i].folder as string).split("/").filter((elm) => elm !== ""),
      ];
    } else {
      path = [studies[i].workspace];
    }
    path.reverse();
    nodeProcess(tree, path);
  }
  return tree;
};

export default {};
