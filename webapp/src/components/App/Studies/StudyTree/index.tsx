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
import { useState } from "react";
import * as api from "../../../../services/api/study";
import useEnqueueErrorSnackbar from "@/hooks/useEnqueueErrorSnackbar";
import useUpdateEffectOnce from "@/hooks/useUpdateEffectOnce";

/**
 * Add a folder that was returned by the explorer into the study tree view.
 *
 * This folder isn't a study, otherwise it wouldn't be
 * returned by the explorer API, but this folder can have study in it
 * and still not be in the initial study tree that's parsed from the study
 * list, this happen when the studies in the folder aren't scanned yet.
 *
 * However we want to allow the user to see these folder. When the user explore
 * they shoudln't wait for a long running scan to complete before they're able to
 * a folder in the hierarchy.
 *
 * @param studiesTree study tree to insert the folder into
 * @param folder folder to inert into the tree
 * @returns study tree with the folder inserted if it wasn't already there.
 * New branch is created if it contain the folder otherwise the branch is left unchanged.
 */
function insertFolderIfNotExist(
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
    if (folderExists) {
      return studiesTree;
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
  }

  // not a direct child, but does belong to this branch so recursively walk though the tree
  return {
    ...studiesTree,
    children: studiesTree.children.map((child) =>
      insertFolderIfNotExist(child, folder),
    ),
  };
}

/**
 * Insert several folders in the study tree if they don't exist already in the tree.
 *
 * @param studiesTree study tree to insert the folder into
 * @param folders folders to inert into the tree
 * @param studiesTree study tree to insert the folder into
 * @param folder folder to inert into the tree
 * @returns study tree with the folder inserted if it wasn't already there.
 * New branch is created if it contain the folder otherwise the branch is left unchanged.
 */
export function insertFoldersIfNotExist(
  studiesTree: StudyTreeNode,
  folders: NonStudyFolder[],
): StudyTreeNode {
  return folders.reduce(
    (tree, folder) => insertFolderIfNotExist(tree, folder),
    studiesTree,
  );
}

/**
 * Call the explorer api to fetch the subfolders under the given path.
 *
 * @param path path of the subfolder to fetch, should sart with root, e.g. root/workspace/folder1
 * @returns list of subfolders under the given path
 */
async function fetchSubfolders(path: string): Promise<NonStudyFolder[]> {
  if (path === "root") {
    // Under root there're workspaces not subfolders
    return [];
  }
  // less than 2 parts means we're at the root level
  const pathParts = path.split("/");
  if (pathParts.length < 2) {
    return [];
  }
  // path parts should be ["root", workspace, "folder1", ...]
  const workspace = pathParts[1];
  const subPath = pathParts.slice(2).join("/");
  return await api.getFolders(workspace, subPath);
}

/**
 * Fetch and insert the subfolders under the given paths into the study tree.
 *
 * This function is used to fill the study tree when the user clicks on a folder.
 *
 * Subfolders are inserted only if they don't exist already in the tree.
 *
 * @param paths list of paths to fetch the subfolders for
 * @param studiesTree study tree to insert the subfolders into
 * @returns study tree with the subfolders inserted if they weren't already there.
 */
async function fetchAndInsertSubfolders(
  paths: string[],
  studiesTree: StudyTreeNode,
): Promise<[StudyTreeNode, string[]]> {
  return paths.reduce(
    async (acc, path) => {
      const [accTree, accFailedPaths] = await acc;
      try {
        const subfolders = await fetchSubfolders(path);
        return [insertFoldersIfNotExist(accTree, subfolders), accFailedPaths];
      } catch (error) {
        console.error("failed to load path ", path, error);
        return [accTree, [...accFailedPaths, path]];
      }
    },
    Promise.resolve<[StudyTreeNode, string[]]>([studiesTree, []]),
  );
}

/**
 * Insert a workspace into the study tree if it doesn't exist already.
 *
 * @param workspace key of the workspace
 * @param stydyTree study tree to insert the workspace into
 * @returns study tree with the empty workspace inserted if it wasn't already there.
 */
function insertWorkspaceIfNotExist(
  stydyTree: StudyTreeNode,
  workspace: string,
) {
  const emptyNode = { name: workspace, path: `/${workspace}`, children: [] };
  if (stydyTree.children.some((child) => child.name === workspace)) {
    return stydyTree;
  }
  return {
    ...stydyTree,
    children: [...stydyTree.children, emptyNode],
  };
}

/**
 * Insert several workspaces into the study tree if they don't exist already in the tree.
 *
 * @param workspaces workspaces to insert into the tree
 * @param stydyTree study tree to insert the workspaces into
 * @returns study tree with the empty workspaces inserted if they weren't already there.
 */
export function insertWorkspacesIfNotExist(
  stydyTree: StudyTreeNode,
  workspaces: string[],
): StudyTreeNode {
  return workspaces.reduce((acc, workspace) => {
    return insertWorkspaceIfNotExist(acc, workspace);
  }, stydyTree);
}

/**
 * fetch and insert the workspaces into the study tree.
 * @param studyTree study tree to insert the workspaces into
 * @returns study tree with the workspaces inserted if they weren't already there.
 */
async function fetchAndInsertWorkspaces(
  studyTree: StudyTreeNode,
): Promise<StudyTreeNode> {
  const workspaces = await api.getWorkspaces();
  return insertWorkspacesIfNotExist(studyTree, workspaces);
}

function StudyTree() {
  const initialStudiesTree = useAppSelector(getStudiesTree);
  const [studiesTree, setStudiesTree] = useState(initialStudiesTree);
  const folder = useAppSelector((state) => getStudyFilters(state).folder, R.T);
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();
  const dispatch = useAppDispatch();

  // Initialize folders once we have the tree
  useUpdateEffectOnce(() => {
    fetchAndInsertWorkspaces(initialStudiesTree)
      .then((tree) => {
        // once we get the workspaces we intialize the first level of folders
        const chidrenPaths = tree.children.map((child) => `root${child.path}`);
        fetchAndInsertSubfolders(chidrenPaths, tree).then((r) => {
          setStudiesTree(r[0]);
          for (const path of r[1]) {
            enqueueErrorSnackbar(
              `Failed to initialize folders for : ${path}`,
              "details in console.error",
            );
          }
        });
      })
      .catch((error) => {
        enqueueErrorSnackbar("Failed to load list workspaces", error);
        setStudiesTree(initialStudiesTree);
      });
  }, [initialStudiesTree]);
  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleTreeItemClick = (
    itemId: string,
    studyTreeNode: StudyTreeNode,
  ) => {
    dispatch(updateStudyFilters({ folder: itemId }));
    if (itemId === "root") {
      fetchAndInsertWorkspaces(studiesTree)
        .then(setStudiesTree)
        .catch((error) => {
          enqueueErrorSnackbar("Failed to load list workspaces", error);
        });
    }
    const chidrenPaths = studyTreeNode.children.map(
      (child) => `root${child.path}`,
    );
    // children paths and current element path
    fetchAndInsertSubfolders(chidrenPaths, studiesTree).then((r) => {
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
          onClick={() => handleTreeItemClick(id, elm)}
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
