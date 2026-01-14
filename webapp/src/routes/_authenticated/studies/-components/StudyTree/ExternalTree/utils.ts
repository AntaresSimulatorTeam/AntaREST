/**
 * Copyright (c) 2026, RTE (https://www.rte-france.com)
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

import { DEFAULT_WORKSPACE_NAME, ROOT_NODE_NAME } from "@/components/utils/constants";
import type { StudyMetadata } from "@/types/types";
import type { ExternalTreeNodeMetadata, FolderDTO, WorkspaceDTO } from "./types";

/**
 * Builds a tree structure from a list of study metadata.
 *
 * @param studies - Array of study metadata objects.
 * @returns A tree structure representing the studies.
 */
export function buildExternalTree(studies: StudyMetadata[]) {
  // It is important to initialize the root node with the default workspace as a child
  // Otherwise we won't see the default workspace if no study has a path (which only
  // happens when a user moves a study to another folder)
  const tree: ExternalTreeNodeMetadata = {
    name: ROOT_NODE_NAME,
    children: [
      {
        name: DEFAULT_WORKSPACE_NAME,
        children: [],
        path: `/${DEFAULT_WORKSPACE_NAME}`,
        isStudyFolder: false,
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
      // add the study folder with the isScannedStudy set to true
      // this flag will be used to not display the study folder in the study tree
      // even if the folder isn't displayed we still need it in the study tree
      // as it makes it easier to distinguish scanned studies from unscanned studies
      if (i === path.length - 1) {
        const studyFolderName = path[i];
        current.children.push({
          name: studyFolderName,
          children: [],
          path: current.path ? `${current.path}/${studyFolderName}` : `/${studyFolderName}`,
          isScannedStudy: true,
        });
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
 * Add a folder that was returned by the explorer into the external tree view.
 *
 * This function doesn't mutate the tree, it returns a new tree with the folder inserted.
 *
 * If the folder is already in the tree, the tree returned will be equal to the tree given to the function.
 *
 * @param tree - external tree to insert the folder into
 * @param folder - folder to insert into the tree
 * @returns external tree with the folder inserted if it wasn't already there.
 * New branch is created if it contain the folder otherwise the branch is left unchanged.
 */
function insertFolderIfNotExist(
  tree: ExternalTreeNodeMetadata,
  folder: FolderDTO,
): ExternalTreeNodeMetadata {
  const currentNodePath = `${tree.path}`;
  // Early return if folder doesn't belong in this branch
  if (!folder.parentPath.startsWith(currentNodePath)) {
    return tree;
  }

  // direct child case
  if (folder.parentPath === currentNodePath) {
    const folderExists = tree.children.find((child) => child.name === folder.name);
    if (folderExists) {
      return {
        ...tree,
        children: [
          ...tree.children.filter((child) => child.name !== folder.name),
          {
            ...folderExists,
            hasChildren: folder.hasChildren,
            isStudyFolder: folder.isStudyFolder,
          },
        ],
      };
    }
    // parent path is the same, but no folder with the same name at this level
    return {
      ...tree,
      children: [
        ...tree.children,
        {
          path: `${folder.parentPath}/${folder.name}`,
          name: folder.name,
          children: [],
          hasChildren: folder.hasChildren,
          isStudyFolder: folder.isStudyFolder,
        },
      ],
    };
  }

  // not a direct child, but does belong to this branch so recursively walk though the tree
  return {
    ...tree,
    children: tree.children.map((child) => insertFolderIfNotExist(child, folder)),
  };
}

/**
 * Insert several folders in the external tree if they don't exist already in the tree.
 *
 * This function doesn't mutate the tree, it returns a new tree with the folders inserted
 *
 * The folders are inserted in the order they are given.
 *
 * @param tree - external tree to insert the folder into
 * @param folders - folders to insert into the tree
 * @returns external tree with the folder inserted if it wasn't already there.
 * New branch is created if it contain the folder otherwise the branch is left unchanged.
 */
export function insertFoldersIfNotExist(
  tree: ExternalTreeNodeMetadata,
  folders: FolderDTO[],
): ExternalTreeNodeMetadata {
  const sortedFolders = [...folders].sort((a, b) => a.path.localeCompare(b.path));
  return sortedFolders.reduce(insertFolderIfNotExist, { ...tree });
}

/**
 * Insert a workspace into the external tree if it doesn't exist already.
 *
 * This function doesn't mutate the tree, it returns a new tree with the workspace inserted.
 *
 * @param workspace - key of the workspace
 * @param tree - external tree to insert the workspace into
 * @returns external tree with the empty workspace inserted if it wasn't already there.
 */
function insertWorkspaceIfNotExist(
  tree: ExternalTreeNodeMetadata,
  workspace: WorkspaceDTO,
): ExternalTreeNodeMetadata {
  const emptyNode = {
    name: workspace.name,
    path: `/${workspace.name}`,
    children: [],
    hasChildren: true,
    alias: workspace.diskName,
  };
  if (tree.children.some((child) => isNodeMatchWorkspace(child, workspace))) {
    return {
      ...tree,
      children: tree.children.map((child) => {
        if (isNodeMatchWorkspace(child, workspace)) {
          return { ...child, alias: workspace.diskName };
        }
        return child;
      }),
    };
  }
  return {
    ...tree,
    children: [...tree.children, emptyNode],
  };
}

function isNodeMatchWorkspace(a: ExternalTreeNodeMetadata, b: WorkspaceDTO): boolean {
  return a.name === b.name;
}

/**
 * Insert several workspaces into the external tree if they don't exist already in the tree.
 *
 * This function doesn't mutate the tree, it returns a new tree with the workspaces inserted.
 *
 * The workspaces are inserted in the order they are given.
 *
 * @param workspaces - workspaces to insert into the tree
 * @param tree - external tree to insert the workspaces into
 * @returns external tree with the empty workspaces inserted if they weren't already there.
 */
export function insertWorkspacesIfNotExist(
  tree: ExternalTreeNodeMetadata,
  workspaces: WorkspaceDTO[],
): ExternalTreeNodeMetadata {
  return workspaces.reduce((acc, workspace) => insertWorkspaceIfNotExist(acc, workspace), {
    ...tree,
  });
}

/**
 * Insert workspaces and folders into the external tree if they don't exist already.
 *
 * This function doesn't mutate the tree, it returns a new tree with the workspaces and folders inserted.
 *
 * @param tree - external tree to insert the workspaces and folders into
 * @param workspaces - workspaces to insert into the tree
 * @param folders - folders to insert into the tree
 * @returns external tree with the workspaces and folders inserted if they weren't already there.
 */
export function insertIfNotExist(
  tree: ExternalTreeNodeMetadata,
  workspaces: WorkspaceDTO[],
  folders: FolderDTO[],
) {
  const treeWithWorkspaces = insertWorkspacesIfNotExist(tree, workspaces);
  const treeWithFolders = insertFoldersIfNotExist(treeWithWorkspaces, folders);
  return treeWithFolders;
}
