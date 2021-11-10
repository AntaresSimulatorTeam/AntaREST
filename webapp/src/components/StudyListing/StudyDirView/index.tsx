import React, { useCallback, useEffect, useState } from 'react';
import { useHistory } from 'react-router-dom';
import { connect, ConnectedProps } from 'react-redux';
import { findNode, StudyTreeNode } from '../utils';
import DirView from './DirView';
import { StudyMetadata } from '../../../common/types';
import { AppState } from '../../../App/reducers';
import { updateFolderPosition } from '../../../ducks/study';

const mapState = (state: AppState) => ({
  directory: state.study.directory,
});

const mapDispatch = ({
  updateFolderPos: updateFolderPosition,
});

const connector = connect(mapState, mapDispatch);
type PropsFromRedux = ConnectedProps<typeof connector>;
interface OwnProps {
  tree: StudyTreeNode;
}
type PropTypes = PropsFromRedux & OwnProps;

const StudyDirView = (props: PropTypes) => {
  const history = useHistory();
  const { tree, updateFolderPos, directory } = props;
  const [dirPath, setDirPath] = useState<Array<string>>([tree.name]);
  const [currentNode, setCurrentNode] = useState<StudyTreeNode>(tree);

  const onClick = (element: StudyTreeNode | StudyMetadata): void => {
    if ((element as StudyMetadata).id === undefined) {
      setCurrentNode(element as StudyTreeNode);
      const newPath: Array<string> = dirPath.concat([element.name]);
      setDirPath(newPath);
      updateFolderPos(newPath.join('/'));
    } else {
      history.push(`/study/${encodeURI((element as StudyMetadata).id)}`);
    }
  };

  const onDirClick = (element: string): void => {
    const { path, node } = findNode(element, tree, []);
    setCurrentNode(node as StudyTreeNode);
    setDirPath(path);
    updateFolderPos(path.join('/'));
  };

  const updateTree = useCallback((element: string, treeElement: StudyTreeNode): void => {
    const { path, node } = findNode(element, treeElement, []);
    if (node !== undefined) {
      setCurrentNode(node);
      setDirPath(path);
    } else {
      setCurrentNode(treeElement);
      setDirPath([treeElement.name]);
    }
  }, []);

  useEffect(() => {
    updateTree(currentNode.name, tree);
  }, [currentNode.name, tree, updateTree]);

  useEffect(() => {
    const tmpTab = directory.split('/');
    if (tmpTab.length > 0) {
      updateTree(tmpTab[tmpTab.length - 1], tree);
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <DirView
      dirPath={dirPath}
      node={currentNode}
      onClick={onClick}
      onDirClick={onDirClick}
    />
  );
};

export default connector(StudyDirView);
