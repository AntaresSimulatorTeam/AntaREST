import moment from 'moment';
import { RawNodeDatum } from 'react-d3-tree/lib/types/common';
import { StudyMetadata } from '../../../common/types';
import { getVariantChildrens, getVariantParents } from '../../../services/api/variant';

export const buildNodeFromMetadata = (study: StudyMetadata): RawNodeDatum =>
  ({
    name: study.name,
    attributes: {
      id: study.id,
      owner: study.owner.name,
      version: study.version,
      creationDate: moment.unix(study.creationDate).format('YYYY/MM/DD HH:mm'),
      modificationDate: moment.unix(study.modificationDate).format('YYYY/MM/DD HH:mm'),
    },
    children: [],
  });

export const buildTree = async (node: RawNodeDatum) => {
  const children: Array<StudyMetadata> = await getVariantChildrens(String(node.attributes?.id));
  if (children.length === 0) return;
  // eslint-disable-next-line no-param-reassign
  node.children = [];
  await Promise.all(
    children.map(async (elm) => {
      const elmNode = buildNodeFromMetadata(elm);
      await buildTree(elmNode);
      if (node.children !== undefined) node.children.push({ ...elmNode });
    }),
  );
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

export default buildTree;
