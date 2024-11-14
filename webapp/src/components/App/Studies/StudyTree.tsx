/**
 * Copyright (c) 2024, RTE (https://www.rte-france.com)
 *
 * See AUTHORS.txt
 *
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/.
 *
 * SPDX-License-Identifier: MPL-2.0
 *
 * This file is part of the Antares project.
 */

import { NonStudyFolder, StudyTreeNode } from "./utils";
import useAppSelector from "../../../redux/hooks/useAppSelector";
import { getStudiesTree, getStudyFilters } from "../../../redux/selectors";
import useAppDispatch from "../../../redux/hooks/useAppDispatch";
import { updateStudyFilters } from "../../../redux/ducks/studies";
import TreeItemEnhanced from "../../common/TreeItemEnhanced";
import { SimpleTreeView } from "@mui/x-tree-view/SimpleTreeView";
import { getParentPaths } from "../../../utils/pathUtils";
import * as R from "ramda";
import { useEffect, useState } from "react";
import * as api from "../../../services/api/study";

/**
 * Add a folder that was returned by the explorer into the study tree view.
 *
 * This folder isn't a study, otherwise it woudl'nt be
 * returned by the explorer API, but this folder can have study in it
 * and still not be in the initial study tree that's parsed from the study
 * list, this happen when the studies in the folder aren't scanned yet.
 *
 * However we want to allow the user to see these folder. When the user explore
 * they shoudln't wait for a long running scan to complete before they're able to
 * a folder in the hierarchy.
 *
 * @param studiesTree
 * @param folder
 * @returns
 */
function mergeStudyTreeAndFolder(
  studiesTree: StudyTreeNode,
  folder: NonStudyFolder,
): StudyTreeNode {
  if (folder.parentPath == studiesTree.path) {
    for (const child of studiesTree.children) {
      if (child.name == folder.name) {
        // parent path is the same, folder name is the same
        // we don't override the existing folder
        // so we return here and don't update this node
        return studiesTree;
      }
    }
    // parent path is the same, but no folder with the same name at this level
    return {
      ...studiesTree,
      children: [
        ...studiesTree.children,
        {
          path: `${folder.parentPath}/${folder.name}`,
          name: folder.name,
          children: [],
        },
      ],
    };
  } else if (folder.parentPath.startsWith(studiesTree.path)) {
    // recursively walk though the tree
    // recursively merge in each child
    return {
      ...studiesTree,
      children: studiesTree.children.map((child) =>
        mergeStudyTreeAndFolder(child, folder),
      ),
    };
  } else {
    // folder isn't part of this hierarchy
    return studiesTree;
  }
}

/**
 * Merge several folders in the study tree.
 *
 * @param studiesTree
 * @param folders
 * @returns
 */
export function mergeStudyTreeAndFolders(
  studiesTree: StudyTreeNode,
  folders: NonStudyFolder[],
): StudyTreeNode {
  for (const folder of folders) {
    studiesTree = mergeStudyTreeAndFolder(studiesTree, folder);
  }
  return studiesTree;
}

async function fetchAndMergeSubfolders(
  path: string,
  studiesTree: StudyTreeNode,
): Promise<StudyTreeNode> {
  if (path === "root") {
    // Under root there're workspaces not subfolders
    return studiesTree;
  }
  const pathParts = path.split("/");
  if (pathParts.length < 2) {
    return studiesTree;
  }
  // path parts should be ["root", workspace, "foler1", ...]
  const workspace = pathParts[1];
  const subPath = pathParts.slice(2).join("/");
  const subFolders = await api.getFolders(workspace, subPath);
  const nextStudiesTree = mergeStudyTreeAndFolders(studiesTree, subFolders);
  return nextStudiesTree;
}

function StudyTree() {
  const emptyNode: StudyTreeNode = { name: "", path: "", children: [] };
  const [studiesTree, setStudiesTree] = useState(emptyNode);
  const [initializedFlag, setInitializedFlag] = useState(false);
  const folder = useAppSelector((state) => getStudyFilters(state).folder, R.T);
  const initialStudiesTree = useAppSelector(getStudiesTree);
  const dispatch = useAppDispatch();

  useEffect(() => {
    if (!initializedFlag) {
      setStudiesTree(initialStudiesTree);
      setInitializedFlag(true);
    }
  }, [studiesTree]);

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleTreeItemClick = (itemId: string) => {
    dispatch(updateStudyFilters({ folder: itemId }));
    fetchAndMergeSubfolders(itemId, studiesTree).then((nextStudiesTree) =>
      setStudiesTree(nextStudiesTree),
    );
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  const buildTree = (children: StudyTreeNode[], parentId?: string) => {
    return children.map((elm) => {
      const id = parentId ? `${parentId}/${elm.name}` : elm.name;

      return (
        <TreeItemEnhanced
          key={id}
          itemId={id}
          label={elm.name}
          onClick={() => handleTreeItemClick(id)}
        >
          {buildTree(elm.children, id)}
        </TreeItemEnhanced>
      );
    });
  };

  return (
    <SimpleTreeView
      defaultExpandedItems={[...getParentPaths(folder), folder]}
      defaultSelectedItems={folder}
      sx={{ flexGrow: 1, height: 0, width: 1, py: 1 }}
    >
      {buildTree([studiesTree])}
    </SimpleTreeView>
  );
}

export default StudyTree;
