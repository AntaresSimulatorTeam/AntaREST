import { RawNodeDatum } from 'react-d3-tree/lib/types/common';
import { StudyMetadata, VariantTree } from '../../../common/types';
import { getVariantChildren, getVariantParents } from '../../../services/api/variant';
import { convertUTCToLocalTime } from '../../../services/utils';

const buildNodeFromMetadata = (study: StudyMetadata): RawNodeDatum =>
  ({
    name: study.name,
    attributes: {
      id: study.id,
      owner: study.owner.name,
      version: study.version,
      creationDate: convertUTCToLocalTime(study.creationDate),
      modificationDate: convertUTCToLocalTime(study.modificationDate),
    },
    children: [],
  });

const convertVariantTreeToNodeDatum = (tree: VariantTree): RawNodeDatum => {
  const nodeDatum = buildNodeFromMetadata(tree.node);
  nodeDatum.children = (tree.children || []).map((el: VariantTree) => convertVariantTreeToNodeDatum(el));
  return nodeDatum;
};

const buildTree = async (node: RawNodeDatum) => {
  const childrenTree: VariantTree = await getVariantChildren(String(node.attributes?.id));
  if ((childrenTree.children || []).length === 0) return;
  // eslint-disable-next-line no-param-reassign
  node.children = convertVariantTreeToNodeDatum(childrenTree).children;
};

export const getTreeNodes = async (study: StudyMetadata): Promise<RawNodeDatum> => {
  const parents = (await getVariantParents(study.id)).reverse();
  const currentNode = buildNodeFromMetadata(study);

  if (parents.length > 0) {
    const rootNode: RawNodeDatum = buildNodeFromMetadata(parents[0]);
    let prevNode: RawNodeDatum = rootNode;

    for (let i = 1; i < parents.length; i += 1) {
      const elmNode = buildNodeFromMetadata(parents[i]);
      if (prevNode.children !== undefined) prevNode.children.push(elmNode);
      prevNode = elmNode;
    }
    await buildTree(currentNode);
    if (prevNode.children !== undefined) prevNode.children.push(currentNode);
    return rootNode;
  }

  await buildTree(currentNode);
  return currentNode;
};

export default {};
