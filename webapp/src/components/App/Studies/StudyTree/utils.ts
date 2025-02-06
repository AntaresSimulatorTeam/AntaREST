/**
 * Copyright (c) 2025, RTE (https://www.rte-france.com)
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

import * as api from "../../../../services/api/study";
import type { StudyMetadata } from "../../../../common/types";
import type { StudyTreeNode, NonStudyFolderDTO } from "./types";

/**
 * Builds a tree structure from a list of study metadata.
 *
 * @param studies - Array of study metadata objects.
 * @returns A tree structure representing the studies.
 */
export function buildStudyTree(studies: StudyMetadata[]) {
  // It is important to initialize the root node with the default workspace as a child
  // Otherwise we won't see the default workspace if no study has a path (which only
  // happens when a user moves a study to another folder)
  const tree: StudyTreeNode = {
    name: "root",
    children: [
      {
        name: "default",
        children: [],
        path: "/default",
      },
    ],
    path: "",
  };

  for (const study of studies) {
    const path =
      typeof study.folder === "string"
        ? [study.workspace, ...study.folder.split("/").filter(Boolean)]
        : [study.workspace];

    let current = tree;

    for (let i = 0; i < path.length; i++) {
      // Skip the last folder, as it represents the study itself
      if (i === path.length - 1) {
        break;
      }

      const folderName = path[i];
      let child = current.children.find((child) => child.name === folderName);

      if (!child) {
        child = {
          name: folderName,
          children: [],
          path: current.path ? `${current.path}/${folderName}` : `/${folderName}`,
        };

        current.children.push(child);
      }

      current = child;
    }
  }

  return tree;
}

/**
 * Add a folder that was returned by the explorer into the study tree view.
 *
 * This function doesn't mutate the tree, it returns a new tree with the folder inserted.
 *
 * If the folder is already in the tree, the tree returnred will be equal to the tree given to the function.
 *
 * @param studiesTree - study tree to insert the folder into
 * @param folder - folder to inert into the tree
 * @returns study tree with the folder inserted if it wasn't already there.
 * New branch is created if it contain the folder otherwise the branch is left unchanged.
 */
function insertFolderIfNotExist(
  studiesTree: StudyTreeNode,
  folder: NonStudyFolderDTO,
): StudyTreeNode {
  const currentNodePath = `${studiesTree.path}`;
  // Early return if folder doesn't belong in this branch
  if (!folder.parentPath.startsWith(currentNodePath)) {
    return studiesTree;
  }

  // direct child case
  if (folder.parentPath == currentNodePath) {
    const folderExists = studiesTree.children.find((child) => child.name === folder.name);
    if (folderExists) {
      return {
        ...studiesTree,
        children: [
          ...studiesTree.children.filter((child) => child.name !== folder.name),
          {
            ...folderExists,
            hasChildren: folder.hasChildren,
          },
        ],
      };
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
          hasChildren: folder.hasChildren,
        },
      ],
    };
  }

  // not a direct child, but does belong to this branch so recursively walk though the tree
  return {
    ...studiesTree,
    children: studiesTree.children.map((child) => insertFolderIfNotExist(child, folder)),
  };
}

/**
 * Insert several folders in the study tree if they don't exist already in the tree.
 *
 * This function doesn't mutate the tree, it returns a new tree with the folders inserted
 *
 * The folders are inserted in the order they are given.
 *
 * @param studiesTree - study tree to insert the folder into
 * @param folders - folders to inert into the tree
 * @param studiesTree - study tree to insert the folder into
 * @param folder - folder to inert into the tree
 * @returns study tree with the folder inserted if it wasn't already there.
 * New branch is created if it contain the folder otherwise the branch is left unchanged.
 */
export function insertFoldersIfNotExist(
  studiesTree: StudyTreeNode,
  folders: NonStudyFolderDTO[],
): StudyTreeNode {
  return folders.reduce((tree, folder) => {
    return insertFolderIfNotExist(tree, folder);
  }, studiesTree);
}

/**
 * Call the explorer api to fetch the subfolders under the given path.
 *
 * @param path - path of the subfolder to fetch, should sart with root, e.g. root/workspace/folder1
 * @returns list of subfolders under the given path
 */
async function fetchSubfolders(path: string): Promise<NonStudyFolderDTO[]> {
  if (path === "root") {
    console.error("this function should not be called with path 'root'", path);
    // Under root there're workspaces not subfolders
    return [];
  }
  if (!path.startsWith("root/")) {
    console.error("path here should start with root/ ", path);
    return [];
  }
  // less than 2 parts means we're at the root level
  const pathParts = path.split("/");
  if (pathParts.length < 2) {
    console.error(
      "this function should not be called with a path that has less than two com",
      path,
    );
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
 * @param paths - list of paths to fetch the subfolders for
 * @param studiesTree - study tree to insert the subfolders into
 * @returns a tuple with study tree with the subfolders inserted if they weren't already there and path for which
 * the fetch failed.
 */
export async function fetchAndInsertSubfolders(
  paths: string[],
  studiesTree: StudyTreeNode,
): Promise<[StudyTreeNode, string[]]> {
  const results = await Promise.allSettled(paths.map((path) => fetchSubfolders(path)));
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
 * @param workspace - key of the workspace
 * @param stydyTree - study tree to insert the workspace into
 * @returns study tree with the empty workspace inserted if it wasn't already there.
 */
function insertWorkspaceIfNotExist(stydyTree: StudyTreeNode, workspace: string): StudyTreeNode {
  const emptyNode = {
    name: workspace,
    path: `/${workspace}`,
    children: [],
  };
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
 * @param workspaces - workspaces to insert into the tree
 * @param stydyTree - study tree to insert the workspaces into
 * @returns study tree with the empty workspaces inserted if they weren't already there.
 */
export function insertWorkspacesIfNotExist(
  stydyTree: StudyTreeNode,
  workspaces: string[],
): StudyTreeNode {
  return workspaces.reduce(
    (acc, workspace) => insertWorkspaceIfNotExist(acc, workspace),
    stydyTree,
  );
}

/**
 * Fetch and insert the workspaces into the study tree.
 *
 * Workspaces are inserted only if they don't exist already in the tree.
 *
 * This function doesn't mutate the tree, it returns a new tree with the workspaces inserted.
 *
 * @param studyTree - study tree to insert the workspaces into
 * @returns study tree with the workspaces inserted if they weren't already there.
 */
export async function fetchAndInsertWorkspaces(studyTree: StudyTreeNode): Promise<StudyTreeNode> {
  const workspaces = await api.getWorkspaces();
  return insertWorkspacesIfNotExist(studyTree, workspaces);
}

/**
 * This function is used when we want to get updates of rTree withouth loosing data from lTree.
 *
 *
 * @param left
 * @param right
 * @returns a new tree with the data from rTree merged into lTree.
 */
export function mergeDeepRightStudyTree(left: StudyTreeNode, right: StudyTreeNode): StudyTreeNode {
  const onlyLeft = left.children.filter(
    (eLeft) => !right.children.some((eRight) => eLeft.name === eRight.name),
  );
  const onlyRight = right.children.filter(
    (eRight) => !left.children.some((eLeft) => eLeft.name === eRight.name),
  );
  const both = innerJoin(left.children, right.children);
  const bothAfterMerge = both.map((e) => mergeDeepRightStudyTree(e[0], e[1]));
  const childrenAfterMerge = [...onlyLeft, ...bothAfterMerge, ...onlyRight];
  return {
    ...right,
    children: childrenAfterMerge,
  };
}

/**
 * This function joins based on the name property.
 *
 * @param left
 * @param right
 * @returns list of tuples where the first element is from the left list and the second element is from the right list.
 */
export function innerJoin(
  left: StudyTreeNode[],
  right: StudyTreeNode[],
): Array<[StudyTreeNode, StudyTreeNode]> {
  return left.reduce<Array<[StudyTreeNode, StudyTreeNode]>>((acc, leftNode) => {
    const matchedRightNode = right.find((rightNode) => rightNode.name === leftNode.name);
    if (matchedRightNode) {
      acc.push([{ ...leftNode }, { ...matchedRightNode }]);
    }
    return acc;
  }, []);
}
