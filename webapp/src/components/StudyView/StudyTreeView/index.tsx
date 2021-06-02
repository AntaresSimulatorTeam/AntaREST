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


const getType = (data : any, path: string, itemkey: string) : GetTypeProps | undefined  => {
  if (typeof data !== 'object')
  {
    const tmp = data.split('://');
    console.log('Path : ',path)
    console.log('Tmp : ',tmp)
    if(tmp && tmp.length > 0)
      return {type: tmp[0] as DataType, icon: 'file-alt', data: `${path}/${itemkey}`};
    else
      return {type: 'file', icon: 'file-alt', data: `${path}/${itemkey}`};
  }
  if(isJsonLeaf(data))
    return {type: 'json', icon: 'file-code', data: JSON.stringify(data)};
  return undefined;
}

type DataType =  'file' | 'json' | 'matrix';

interface GetTypeProps {
  type: DataType;
  icon: 'file-alt' | 'file-code';
  data: string;
}

interface ItemPropTypes {
  itemkey: string;
  data: any;
  path?: string;
  viewer: (type: DataType, data: string) => void;
}

const StudyTreeItem = (props: ItemPropTypes) => {
  const { itemkey, data, path = '/', viewer } = props;

  // if not an object then it's a RawFileNode or MatrixNode
  // here we have to decide which viewer to use
    const params = getType(data, path, itemkey);
    if(!!params)
    {
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
  view: (type: DataType, data: string) => void;
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
