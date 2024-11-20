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
import useEnqueueErrorSnackbar from "@/hooks/useEnqueueErrorSnackbar";
import { set } from "lodash";

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
  // path parts should be ["root", workspace, "folder1", ...]
  const workspace = pathParts[1];
  const subPath = pathParts.slice(2).join("/");
  const subFolders = await api.getFolders(workspace, subPath);
  const nextStudiesTree = mergeStudyTreeAndFolders(studiesTree, subFolders);
  return nextStudiesTree;
}

async function fetchAndMergeSubfoldersForPaths( // reduce try catch (
  paths: string[],
  studiesTree: StudyTreeNode,
): Promise<[StudyTreeNode, string[]]> {
  return paths.reduce<Promise<[StudyTreeNode, string[]]>>(
    async (acc, path) => {
      const accRes = await acc;
      const accTree: StudyTreeNode = accRes[0];
      const accFailedPaths: string[] = accRes[1];
      try {
        return [await fetchAndMergeSubfolders(path, accTree), accFailedPaths];
      } catch (error) {
        console.error("failed to load path ", path, error);
        return [accTree, [...accFailedPaths, path]];
      }
    },
    Promise.resolve([studiesTree, []]),
  );
}

function mergeNewWorkspace(workspace: string, stydyTree: StudyTreeNode) {
  const emptyNode = { name: workspace, path: `/${workspace}`, children: [] };
  if (stydyTree.children.some((child) => child.name === workspace)) {
    return stydyTree;
  }
  return {
    ...stydyTree,
    children: [...stydyTree.children, emptyNode],
  };
}

function mergeNewWorkspaces(
  workspaces: string[],
  stydyTree: StudyTreeNode,
): StudyTreeNode {
  return workspaces.reduce((acc, workspace) => {
    return mergeNewWorkspace(workspace, acc);
  }, stydyTree);
}

function getStudyTreeNode(
  path: string,
  stydyTree: StudyTreeNode,
): StudyTreeNode | null {
  // path always start with root
  const studyTreePath = `root${stydyTree.path}`;
  if (studyTreePath === path) {
    return stydyTree;
  }
  let result: StudyTreeNode | null = null;
  for (const child of stydyTree.children) {
    result = getStudyTreeNode(path, child);
    if (result) {
      return result;
    }
  }
  return null;
}

function StudyTree() {
  const initialStudiesTree = useAppSelector(getStudiesTree);
  const [studiesTree, setStudiesTree] = useState(initialStudiesTree);
  const folder = useAppSelector((state) => getStudyFilters(state).folder, R.T);
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();
  const dispatch = useAppDispatch();

  // Initialize folders once we have the tree
  useEffect(() => {
    if (!folder || !initialStudiesTree.children.length) {
      return;
    }
    api
      .getWorkspaces()
      .then((workspaces) => {
        setStudiesTree(mergeNewWorkspaces(workspaces, initialStudiesTree));
      })
      .catch((error) => {
        enqueueErrorSnackbar("Failed to load list workspaces", error);
        setStudiesTree(initialStudiesTree);
      });
  }, [folder, initialStudiesTree]);
  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleTreeItemClick = (itemId: string) => {
    dispatch(updateStudyFilters({ folder: itemId }));
    const currentNode = getStudyTreeNode(itemId, studiesTree);
    if (!currentNode) {
      console.error("Clicked on a non existing node", itemId);
      return;
    }
    const chidrenPaths = currentNode.children.map(
      (child) => `root${child.path}`,
    );
    fetchAndMergeSubfoldersForPaths(chidrenPaths, studiesTree).then((r) => {
      setStudiesTree(r[0]);
      for (const path of r[1]) {
        enqueueErrorSnackbar(
          `Failed to initialize folders for : ${path}`,
          "details in console.error",
        );
      }
    });
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
