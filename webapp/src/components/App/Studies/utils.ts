/* eslint-disable no-plusplus */
import { StudyMetadata } from "../../../common/types";

export interface StudyTreeNode {
  name: string;
  path: string;
  children: Array<StudyTreeNode>;
}

const nodeProcess = (
  tree: StudyTreeNode,
  path: Array<string>,
  folderPath: string
): void => {
  const { children } = tree;
  if (path.length === 1) {
    return;
  }
  const element = path.pop() || "";
  const index = children.findIndex(
    (elm: StudyTreeNode) => elm.name === element
  );
  const newFolderPath = `${folderPath}/${element}`;
  if (index < 0) {
    children.push({ name: element, children: [], path: newFolderPath });
    nodeProcess(
      children[children.length - 1] as StudyTreeNode,
      path,
      newFolderPath
    );
  } else {
    nodeProcess(children[index] as StudyTreeNode, path, newFolderPath);
  }
};

export const buildStudyTree = (
  studies: Array<StudyMetadata>
): StudyTreeNode => {
  const tree: StudyTreeNode = { name: "root", children: [], path: "" };
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
    nodeProcess(tree, path, "");
  }
  return tree;
};
