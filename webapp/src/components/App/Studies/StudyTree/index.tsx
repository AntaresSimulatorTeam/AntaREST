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

import { NonStudyFolder, StudyTreeNode } from ".././utils";
import useAppSelector from "../../../../redux/hooks/useAppSelector";
import { getStudiesTree, getStudyFilters } from "../../../../redux/selectors";
import useAppDispatch from "../../../../redux/hooks/useAppDispatch";
import { updateStudyFilters } from "../../../../redux/ducks/studies";
import TreeItemEnhanced from "../../../common/TreeItemEnhanced";
import { SimpleTreeView } from "@mui/x-tree-view/SimpleTreeView";
import { getParentPaths } from "../../../../utils/pathUtils";
import * as R from "ramda";
import { useEffect, useState } from "react";
import * as api from "../../../../services/api/study";

/**
 * Add a folder that was returned by the explorer into the study tree view.
 *
 * This folder isn't a study, otherwise it would'nt be
 * returned by the explorer API, but this folder can have study in it
 * and still not be in the initial study tree that's parsed from the study
 * list, this happen when the studies in the folder aren't scanned yet.
 *
 * However we want to allow the user to see these folder. When the user explore
 * they shoudln't wait for a long running scan to complete before they're able to
 * a folder in the hierarchy.
 *
 * @param studiesTree study tree to merge the folder into
 * @param folder folder to merge into the tree
 * @returns
 */
function mergeStudyTreeAndFolder(
  studiesTree: StudyTreeNode,
  folder: NonStudyFolder,
): StudyTreeNode {
  // Early return if folder doesn't belong in this branch
  if (!folder.parentPath.startsWith(studiesTree.path)) {
    return studiesTree;
  }

  // direct child case
  if (folder.parentPath == studiesTree.path) {
    const folderExists = studiesTree.children.some(
      (child) => child.name === folder.name,
    );
    if (folderExists) return studiesTree;

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
  }

  // not a direct child, but does belong to this branch so recursively walk though the tree
  return {
    ...studiesTree,
    children: studiesTree.children.map((child) =>
      mergeStudyTreeAndFolder(child, folder),
    ),
  };
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
  return folders.reduce(
    (tree, folder) => mergeStudyTreeAndFolder(tree, folder),
    studiesTree,
  );
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
  const initialStudiesTree = useAppSelector(getStudiesTree);
  const [studiesTree, setStudiesTree] = useState(initialStudiesTree);
  // const [initializedFlag, setInitializedFlag] = useState(false);
  const folder = useAppSelector((state) => getStudyFilters(state).folder, R.T);
  const dispatch = useAppDispatch();

  // useEffect(() => {
  //   if (!initializedFlag) {
  //     setStudiesTree(initialStudiesTree);
  //     setInitializedFlag(true);
  //   }
  // }, [studiesTree]);

  // Initialize folders once we have the tree
  useEffect(() => {
    if (!folder || !initialStudiesTree.children.length) {
      return;
    }

    // extract folder paths excluding root
    const getFolderPaths = (path: string): string[] =>
      path.split("/").reduce<string[]>((acc, _, i, parts) => {
        const currentPath = parts.slice(0, i + 1).join("/");
        return currentPath !== "root" ? [...acc, currentPath] : acc;
      }, []);

    // sequential folder fetching with error handling
    const updateFolderTree = async () => {
      try {
        const finalTree = await getFolderPaths(folder).reduce(
          async (treePromise, path) => {
            const tree = await treePromise;
            return fetchAndMergeSubfolders(path, tree);
          },
          Promise.resolve(initialStudiesTree),
        );

        setStudiesTree(finalTree);
      } catch (error) {
        // here you can use a snackback error component if needed
        console.error("Failed to initialize folders:", error);
      }
    };

    updateFolderTree();
  }, [folder, initialStudiesTree]);
  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleTreeItemClick = (itemId: string) => {
    dispatch(updateStudyFilters({ folder: itemId }));
    fetchAndMergeSubfolders(itemId, studiesTree).then(setStudiesTree);
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
