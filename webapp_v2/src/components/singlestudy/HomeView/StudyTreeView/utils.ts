import { StudyMetadata, VariantTree } from '../../../../common/types';
import { getVariantChildren, getVariantParents } from '../../../../services/api/variant';
import { convertUTCToLocalTime } from '../../../../services/utils';

export interface StudyTree {
    name: string;
    attributes: {
        id: string;
        modificationDate: string;
    }
    children: Array<StudyTree>;
}

const buildNodeFromMetadata = (study: StudyMetadata): StudyTree =>
  ({
    name: study.name,
    attributes: {
      id: study.id,
      modificationDate: convertUTCToLocalTime(study.modificationDate),
    },
    children: [],
  });

const convertVariantTreeToStudyTree = (tree: VariantTree): StudyTree => {
  const nodeDatum = buildNodeFromMetadata(tree.node);
  nodeDatum.children = (tree.children || []).map((el: VariantTree) => convertVariantTreeToStudyTree(el));
  return nodeDatum;
};

const buildTree = async (node: StudyTree, childrenTree: VariantTree) : Promise<void> => {
  if ((childrenTree.children || []).length === 0) return;
  // eslint-disable-next-line no-param-reassign
  node.children = convertVariantTreeToStudyTree(childrenTree).children;
};

export const getTreeNodes = async (study: StudyMetadata, parentsStudy: Array<StudyMetadata>, childrenTree: VariantTree): Promise<StudyTree> => {
  const parents = parentsStudy.reverse();
  const currentNode = buildNodeFromMetadata(study);

  if (parents.length > 0) {
    const rootNode: StudyTree = buildNodeFromMetadata(parents[0]);
    let prevNode: StudyTree = rootNode;

    for (let i = 1; i < parents.length; i += 1) {
      const elmNode = buildNodeFromMetadata(parents[i]);
      if (prevNode.children !== undefined) prevNode.children.push(elmNode);
      prevNode = elmNode;
    }
    await buildTree(currentNode, childrenTree);
    if (prevNode.children !== undefined) prevNode.children.push(currentNode);
    return rootNode;
  }

  await buildTree(currentNode, childrenTree);
  return currentNode;
};

export default {};
