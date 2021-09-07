import moment from 'moment';
import { RawNodeDatum } from 'react-d3-tree/lib/types/common';
import { StudyMetadata } from '../../../common/types';
import { getVariantChildrens } from '../../../services/api/variant';

export const buildNodeFromMetadata = (study: StudyMetadata): RawNodeDatum =>
  /* export interface StudyMetadata {
        id: string;
        name: string;
        creationDate: number;
        modificationDate: number;
        owner: StudyMetadataOwner;
        version: string;
        workspace: string;
        managed: boolean;
        archived: boolean;
        groups: Array<{ id: string; name: string }>;
        publicMode: StudyPublicMode;
      } */
  ({
    name: study.name,
    attributes: {
      id: study.id,
      owner: study.owner?.id || '',
      creationDate: moment.unix(study.creationDate).format('YYYY/MM/DD HH:mm'),
    },
    children: [],
  });

export const buildTree = async (node: RawNodeDatum) => {
  const children = await getVariantChildrens(String(node.attributes?.id));
  console.log('ID: ', node.attributes?.id, ', CHILDREN: ', children);
  if (children.length === 0) return;

  // eslint-disable-next-line no-param-reassign
  node.children = [];
  Promise.all(
    children.map(async (elm) => {
      const elmNode = buildNodeFromMetadata(elm);
      await buildTree(elmNode);
      if (node.children) node.children.push(elmNode);
    }),
  );
};

export default buildTree;
