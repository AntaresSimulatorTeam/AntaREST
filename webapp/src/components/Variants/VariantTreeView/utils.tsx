import moment from 'moment';
import { RawNodeDatum } from 'react-d3-tree/lib/types/common';
import { StudyMetadata } from '../../../common/types';
import { getVariantChildrens } from '../../../services/api/variant';

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

export default buildTree;
