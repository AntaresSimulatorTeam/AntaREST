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

import { NonStudyFolderDTO, StudyTreeNode } from "../utils";
import * as api from "../../../../services/api/study";

/**
 * Add a folder that was returned by the explorer into the study tree view.
 *
 * This function doesn't mutate the tree, it returns a new tree with the folder inserted.
 *
 * If the folder is already in the tree, the tree returnred will be equal to the tree given to the function.
 *
 * @param studiesTree study tree to insert the folder into
 * @param folder folder to inert into the tree
 * @returns study tree with the folder inserted if it wasn't already there.
 * New branch is created if it contain the folder otherwise the branch is left unchanged.
 */
function insertFolderIfNotExist(
  studiesTree: StudyTreeNode,
  folder: NonStudyFolderDTO,
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
 * This function doesn't mutate the tree, it returns a new tree with the folders inserted
 *
 * The folders are inserted in the order they are given.
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
  folders: NonStudyFolderDTO[],
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
async function fetchSubfolders(path: string): Promise<NonStudyFolderDTO[]> {
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
  return api.getFolders(workspace, subPath);
}

/**
 * Fetch and insert the subfolders under the given paths into the study tree.
 *
 * This function is used to fill the study tree when the user clicks on a folder.
 *
 * Subfolders are inserted only if they don't exist already in the tree.
 *
 * This function doesn't mutate the tree, it returns a new tree with the subfolders inserted
 *
 * @param paths list of paths to fetch the subfolders for
 * @param studiesTree study tree to insert the subfolders into
 * @returns a tuple with study tree with the subfolders inserted if they weren't already there and path for which
 * the fetch failed.
 */
export async function fetchAndInsertSubfolders(
  paths: string[],
  studiesTree: StudyTreeNode,
): Promise<[StudyTreeNode, string[]]> {
  const results = await Promise.allSettled(
    paths.map((path) => fetchSubfolders(path)),
  );

  return results.reduce<[StudyTreeNode, string[]]>(
    ([tree, failed], result, index) => {
      if (result.status === "fulfilled") {
        return [insertFoldersIfNotExist(tree, result.value), failed];
      }
      console.error("Failed to load path:", paths[index], result.reason);
      return [tree, [...failed, paths[index]]];
    },
    [studiesTree, []],
  );
}

/**
 * Insert a workspace into the study tree if it doesn't exist already.
 *
 * This function doesn't mutate the tree, it returns a new tree with the workspace inserted.
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
 * This function doesn't mutate the tree, it returns a new tree with the workspaces inserted.
 *
 * The workspaces are inserted in the order they are given.
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
 * Fetch and insert the workspaces into the study tree.
 *
 * Workspaces are inserted only if they don't exist already in the tree.
 *
 * This function doesn't mutate the tree, it returns a new tree with the workspaces inserted.
 *
 * @param studyTree study tree to insert the workspaces into
 * @returns study tree with the workspaces inserted if they weren't already there.
 */
export async function fetchAndInsertWorkspaces(
  studyTree: StudyTreeNode,
): Promise<StudyTreeNode> {
  const workspaces = await api.getWorkspaces();
  return insertWorkspacesIfNotExist(studyTree, workspaces);
}
