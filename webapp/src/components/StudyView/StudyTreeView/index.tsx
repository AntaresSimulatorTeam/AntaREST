/* eslint-disable jsx-a11y/interactive-supports-focus */
/* eslint-disable jsx-a11y/click-events-have-key-events */
import React from 'react';
import TreeView from '@material-ui/lab/TreeView';
import ExpandMoreIcon from '@material-ui/icons/ExpandMore';
import ChevronRightIcon from '@material-ui/icons/ChevronRight';
import TreeItem from '@material-ui/lab/TreeItem';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { StudyDataType } from '../../../common/types';
import { getStudyParams } from './utils';

interface ItemPropTypes {
  itemkey: string;
  data: any;
  path?: string;
  viewer: (type: StudyDataType, data: string) => void;
}

const StudyTreeItem = (props: ItemPropTypes) => {
  const { itemkey, data, path = '/', viewer } = props;

  // if not an object then it's a RawFileNode or MatrixNode
  // here we have to decide which viewer to use
  const params = getStudyParams(data, path, itemkey);
  if (params) {
    return (
      <TreeItem
        nodeId={`${path}/${itemkey}`}
        label={(
          <div role="button" onClick={() => viewer(params.type, params.data)}>
            <FontAwesomeIcon icon={params.icon} />
            <span style={{ marginLeft: '4px' }}>{itemkey}</span>
          </div>
          )}
      />
    );
  }

  // else this is a folder containing.. stuff (recursion)
  return (
    <TreeItem nodeId={`${path}/${itemkey}`} label={itemkey}>
      {Object.keys(data).map((childkey) => (
        <StudyTreeItem key={childkey} itemkey={childkey} data={data[childkey]} path={`${path}/${itemkey}`} viewer={viewer} />
      ))}
    </TreeItem>
  );
};

interface PropTypes {
  data: any;
  view: (type: StudyDataType, data: string) => void;
}

const StudyTreeView = (props: PropTypes) => {
  const { data, view } = props;
  return (
    <TreeView
      multiSelect
      defaultCollapseIcon={<ExpandMoreIcon />}
      defaultExpandIcon={<ChevronRightIcon />}
    >
      {Object.keys(data).map((key) => (<StudyTreeItem key={key} itemkey={key} data={data[key]} viewer={view} />))}
    </TreeView>
  );
};

StudyTreeItem.defaultProps = {
  path: '/',
};

export default StudyTreeView;
