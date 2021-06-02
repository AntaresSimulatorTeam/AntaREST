/* eslint-disable jsx-a11y/interactive-supports-focus */
/* eslint-disable jsx-a11y/click-events-have-key-events */
import React from 'react';
import TreeView from '@material-ui/lab/TreeView';
import ExpandMoreIcon from '@material-ui/icons/ExpandMore';
import ChevronRightIcon from '@material-ui/icons/ChevronRight';
import TreeItem from '@material-ui/lab/TreeItem';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';


const isJsonLeaf = (studyDataNode: any) => {
  // this is a non robust guess work
  const childrenKeys = Object.keys(studyDataNode);
  for (let index = 0; index < childrenKeys.length; index += 1) {
    const element = studyDataNode[childrenKeys[index]];
    // here if one the child of the current node is not an object (so it's a string or an array) and this string is not a file
    // this means this object is like {"a": "something"} or {"a": ["b","c"]} 
    // BUT it could be something like {"a": "something", "b": {"c": "file://xxx"}}} so a kind of hybrid between a folder and a leaf node
    // though I guess this is not possible but i'm not sure...
    // the idea is that if all children is an object or a "file://", it is to be considered a folder
    if (typeof element !== 'object' && (typeof element !== 'string' || !element.startsWith('file:/'))) {
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
  // if not an object then it's a RawFileNode or MatrixNode
  // here we have to decide which viewer to use
  if (typeof data !== 'object') {
    return (
      <TreeItem
        nodeId={`${path}/${itemkey}`}
        label={(
          <div role="button" onClick={() => viewer('file', `${path}/${itemkey}`)}>
            <FontAwesomeIcon icon="file-alt" />
            <span style={{ marginLeft: '4px' }}>{itemkey}</span>
          </div>
        )}
      />
    );
  }

  // check if this can be considered an leaf to be displayed with the json viewer
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
