import React, { useCallback, useEffect, useState } from 'react';
import { useHistory } from 'react-router-dom';
import { connect, ConnectedProps } from 'react-redux';
import { countAllStudies, findNode, isDir, StudyTreeNode } from '../utils';
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
  setCurrentStudiesLength: (length: number) => void;
  launchStudy: (study: StudyMetadata) => void;
  deleteStudy: (study: StudyMetadata) => void;
  importStudy: (study: StudyMetadata, withOutputs: boolean) => void;
  archiveStudy: (study: StudyMetadata) => void;
  unarchiveStudy: (study: StudyMetadata) => void;
}
type PropTypes = PropsFromRedux & OwnProps;

const StudyDirView = (props: PropTypes) => {
  const history = useHistory();
  const { tree, updateFolderPos, directory, setCurrentStudiesLength, importStudy, launchStudy, deleteStudy, archiveStudy, unarchiveStudy } = props;
  const [dirPath, setDirPath] = useState<Array<string>>([tree.name]);
  const [currentNode, setCurrentNode] = useState<StudyTreeNode>(tree);

  const onClick = (element: StudyTreeNode | StudyMetadata): void => {
    if (isDir(element)) {
      setCurrentNode(element as StudyTreeNode);
      setCurrentStudiesLength(countAllStudies(element as StudyTreeNode));
      const newPath: Array<string> = dirPath.concat([element.name]);
      setDirPath(newPath);
      updateFolderPos(newPath.join('/'));
    } else {
      history.push(`/study/${encodeURI((element as StudyMetadata).id)}`);
    }
  };

  const onDirClick = (elements: Array<string>): void => {
    const node = findNode([tree], elements);
    setCurrentNode(node as StudyTreeNode);
    setCurrentStudiesLength(countAllStudies(node as StudyTreeNode));
    setDirPath(elements);
    updateFolderPos(elements.join('/'));
  };

  const updateTree = useCallback((element: Array<string>, treeElement: StudyTreeNode): void => {
    const node = findNode([treeElement], element);
    if (node !== undefined) {
      setCurrentNode(node);
      setCurrentStudiesLength(countAllStudies(node as StudyTreeNode));
      setDirPath(element);
    } else {
      setCurrentNode(treeElement);
      setCurrentStudiesLength(-1);
      setDirPath([treeElement.name]);
    }
  }, [setCurrentStudiesLength]);

  useEffect(() => {
    updateTree(dirPath, tree);
  }, [dirPath, tree, updateTree]);

  useEffect(() => {
    const tmpTab = directory.split('/');
    if (tmpTab.length > 0) {
      updateTree(tmpTab, tree);
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <DirView
      dirPath={dirPath}
      node={currentNode}
      onClick={onClick}
      onDirClick={onDirClick}
      importStudy={importStudy}
      launchStudy={launchStudy}
      deleteStudy={deleteStudy}
      archiveStudy={archiveStudy}
      unarchiveStudy={unarchiveStudy}
    />
  );
};

export default connector(StudyDirView);
