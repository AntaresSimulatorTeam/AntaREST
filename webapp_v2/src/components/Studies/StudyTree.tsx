import React, { useCallback } from 'react';
import TreeView from '@mui/lab/TreeView';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import ChevronRightIcon from '@mui/icons-material/ChevronRight';
import TreeItem from '@mui/lab/TreeItem';
import { StudyTreeNode } from './utils';

interface Props {
    tree: StudyTreeNode;
    folder: string;
    setFolder: (folder: string) => void;
}

function StudyTree(props: Props) {
  const { tree, folder, setFolder } = props;

  const getExpandedTab = (nodeId: string): Array<string> => {
    const expandedTab : Array<string> = [];
    const tab = nodeId.split('/');
    let lastnodeId = '';
    for (let i = 0; i < tab.length; i++) {
      lastnodeId += (i === 0) ? tab[i] : `/${tab[i]}`;
      expandedTab.push(lastnodeId);
    }
    return expandedTab;
  };

  const buildTree = (children: Array<StudyTreeNode>, parentId: string) => children.map((elm) => {
    const newId = `${parentId}/${elm.name}`;
    const elements = buildTree((elm as StudyTreeNode).children, newId).filter((item) => item);
    return (
      <TreeItem
        key={newId}
        nodeId={newId}
        label={elm.name}
        expandIcon={elements.length > 0 ? <ExpandMoreIcon /> : undefined}
        collapseIcon={elements.length > 0 ? <ChevronRightIcon /> : undefined}
        onClick={() => setFolder(newId)}
      >
        {buildTree((elm as StudyTreeNode).children, newId)}
      </TreeItem>
    );
  });
  const getDefaultSelected = useCallback(() => [folder], []);

  const getDefaultExpanded = useCallback(() => getExpandedTab(folder), []);

  return (
    <TreeView
      aria-label="Study tree"
      defaultSelected={getDefaultSelected()}
      defaultExpanded={getDefaultExpanded()}
      selected={[folder]}
      sx={{ flexGrow: 1, height: 0, width: '100%', py: 1 }}
    >
      <TreeItem
        nodeId={tree.name}
        label={tree.name}
        onClick={() => setFolder(tree.name)}
        expandIcon={tree.children.length > 0 ? <ExpandMoreIcon /> : undefined}
        collapseIcon={tree.children.length > 0 ? <ChevronRightIcon /> : undefined}
      >
        {buildTree(tree.children, tree.name)}
      </TreeItem>
    </TreeView>
  );
}

export default StudyTree;
