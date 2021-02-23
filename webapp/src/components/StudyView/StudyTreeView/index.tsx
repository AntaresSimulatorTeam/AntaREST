/* eslint-disable jsx-a11y/interactive-supports-focus */
/* eslint-disable jsx-a11y/click-events-have-key-events */
import React from 'react';
import TreeView from '@material-ui/lab/TreeView';
import ExpandMoreIcon from '@material-ui/icons/ExpandMore';
import ChevronRightIcon from '@material-ui/icons/ChevronRight';
import TreeItem from '@material-ui/lab/TreeItem';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';


const isJsonLeaf = (studyDataNode: any) => {
  const childrenKeys = Object.keys(studyDataNode);
  for (let index = 0; index < childrenKeys.length; index += 1) {
    const element = studyDataNode[childrenKeys[index]];
    if (typeof element !== 'object' && (typeof element !== 'string' || !element.startsWith('file/'))) {
      return true;
    }
  }
  return false;
};

interface ItemPropTypes {
  itemkey: string;
  data: any;
  path?: string;
  viewer: (type: 'file' | 'json', data: string) => void;
}

const StudyTreeItem = (props: ItemPropTypes) => {
  const { itemkey, data, path = '/', viewer } = props;
  if (typeof data !== 'object') {
    return (
      <TreeItem
        nodeId={`${path}/${itemkey}`}
        label={(
          <div role="button" onClick={() => viewer('file', data as string)}>
            <FontAwesomeIcon icon="file-alt" />
            <span style={{ marginLeft: '4px' }}>{itemkey}</span>
          </div>
        )}
      />
    );
  }

  if (isJsonLeaf(data)) {
    return (
      <TreeItem
        nodeId={`${path}/${itemkey}`}
        label={(
          <div role="button" onClick={() => viewer('json', JSON.stringify(data))}>
            <FontAwesomeIcon icon="file-code" />
            <span style={{ marginLeft: '4px' }}>{itemkey}</span>
          </div>
        )}
      />
    );
  }

  return (
    <TreeItem nodeId={`${path}/${itemkey}`} label={itemkey}>
      {Object.keys(data).map((childkey) => (
        <StudyTreeItem key={childkey} itemkey={childkey} data={data[childkey]} path={`${path}/${itemkey}/${childkey}`} viewer={viewer} />
      ))}
    </TreeItem>
  );
};

interface PropTypes {
  data: any;
  view: (type: 'file' | 'json', data: string) => void;
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

export default StudyTreeView;
