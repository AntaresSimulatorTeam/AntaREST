/* eslint-disable jsx-a11y/interactive-supports-focus */
/* eslint-disable jsx-a11y/click-events-have-key-events */
import debug from 'debug';
import React, { useState } from 'react';
import TreeView from '@material-ui/lab/TreeView';
import ExpandMoreIcon from '@material-ui/icons/ExpandMore';
import ChevronRightIcon from '@material-ui/icons/ChevronRight';
import TreeItem from '@material-ui/lab/TreeItem';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { useSnackbar } from 'notistack';
import { CircularProgress } from '@material-ui/core';
import { Translation } from 'react-i18next';
import { getStudyData } from '../../../services/api/study';
import { updateData, isUnloaded } from './utils';

const logError = debug('antares:studytreeview:error');

const isJsonLeaf = (studyDataNode: any) => {
  if (isUnloaded(studyDataNode)) {
    return false;
  }
  const childrenKeys = Object.keys(studyDataNode);
  for (let index = 0; index < childrenKeys.length; index += 1) {
    const element = studyDataNode[childrenKeys[index]];
    if (typeof element !== 'object' && (typeof element !== 'string' || (!element.startsWith('file/') && !element.startsWith('_Unloaded')))) {
      return true;
    }
  }
  return false;
};

interface ItemPropTypes {
  itemkey: string;
  data: any;
  path?: string;
  viewer: (type: 'file' | 'json', dataref: string) => void;
}

const StudyTreeItem = (props: ItemPropTypes) => {
  const { itemkey, data, path = '', viewer } = props;
  const [loading, setLoading] = useState(false);

  if (typeof data !== 'object' && data.startsWith('_Unloaded')) {
    switch (data) {
      case '_UnloadedFolderNode':
        return (
          <TreeItem
            nodeId={`${path}/${itemkey}`}
            label={(
              <span style={{ display: 'flex', alignItems: 'center' }}>
                {loading && <CircularProgress size="0.9em" style={{ marginRight: '0.2em' }} />}
                {itemkey}
              </span>
            )}
            onClick={() => setLoading(true)}
          >
            <TreeItem nodeId={`${path}/${itemkey}/lazy`} label="lazy" />
          </TreeItem>
        );
      case '_UnloadedIniFileNode':
        return (
          <TreeItem
            nodeId={`${path}/${itemkey}`}
            label={(
              <div role="button" onClick={() => viewer('json', `${path}/${itemkey}`)}>
                <FontAwesomeIcon icon="file-code" />
                <span style={{ marginLeft: '4px' }}>{itemkey}</span>
              </div>
              )}
          />
        );
      case '_UnloadedRawFileNode':
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
      default:
        throw Error('Unhandled file type');
    }
  }

  return (
    <TreeItem nodeId={`${path}/${itemkey}`} label={itemkey}>
      {Object.keys(data).map((childkey) => (
        <StudyTreeItem key={childkey} itemkey={childkey} data={data[childkey]} path={`${path}/${itemkey}`} viewer={viewer} />
      ))}
    </TreeItem>
  );
};

interface PropTypes {
  id: string;
  data: any;
  view: (type: 'file' | 'json', data: string) => void;
}

const StudyTreeView = (props: PropTypes) => {
  const { id, data, view } = props;
  const { enqueueSnackbar } = useSnackbar();
  const [fullData, setFullData] = useState(data);
  const [loadedPaths, setLoadedPaths] = useState<string[]>([]);
  const [expanded, setExpanded] = React.useState<string[]>([]);

  const handleToggle = (event: React.ChangeEvent<{}>, nodeIds: string[]) => {
    const toLoad = nodeIds.filter((el) => expanded.indexOf(el) === -1);
    if (toLoad.length === 1 && loadedPaths.indexOf(toLoad[0]) === -1) {
      (async () => {
        try {
          const itemdata = await getStudyData(id, toLoad[0], 1);
          setFullData(updateData(fullData, toLoad[0], itemdata));
          setLoadedPaths(loadedPaths.concat(toLoad[0]));
        } catch (e) {
          logError('Failed to load data', toLoad[0], e);
          enqueueSnackbar(<Translation>{(t) => t('studymanager:failtoretrievedata')}</Translation>, { variant: 'error' });
        }
        setExpanded(nodeIds);
      })();
    } else {
      // node removed or already loaded node
      setExpanded(nodeIds);
    }
  };

  return (
    <TreeView
      multiSelect
      expanded={expanded}
      onNodeToggle={handleToggle}
      defaultCollapseIcon={<ExpandMoreIcon />}
      defaultExpandIcon={<ChevronRightIcon />}
    >
      {Object.keys(fullData).map((key) => (<StudyTreeItem key={key} itemkey={key} data={fullData[key]} viewer={view} />))}
    </TreeView>
  );
};

export default StudyTreeView;
