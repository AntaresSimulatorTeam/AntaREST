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

import { DEFAULT_WORKSPACE_NAME, ROOT_NODE_NAME } from "@/components/common/utils/constants";
import * as api from "../../../../services/api/study";
import type { StudyMetadata } from "../../../../types/types";
import type { FolderDTO, StudyTreeNode, WorkspaceDTO } from "./types";
import type { StudyEventPayload } from "@/services/webSocket/types";
import storage, { StorageKey } from "@/services/utils/localStorage";

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
      // as it makes it easier to distinguish scanned studies from unscanend studies
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
function insertFolderIfNotExist(studiesTree: StudyTreeNode, folder: FolderDTO): StudyTreeNode {
  const currentNodePath = `${studiesTree.path}`;
  // Early return if folder doesn't belong in this branch
  if (!folder.parentPath.startsWith(currentNodePath)) {
    return studiesTree;
  }

  // direct child case
  if (folder.parentPath === currentNodePath) {
    const folderExists = studiesTree.children.find((child) => child.name === folder.name);
    if (folderExists) {
      return {
        ...studiesTree,
        children: [
          ...studiesTree.children.filter((child) => child.name !== folder.name),
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
      ...studiesTree,
      children: [
        ...studiesTree.children,
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
  folders: FolderDTO[],
): StudyTreeNode {
  const sortedFolders = [...folders].sort((a, b) => a.path.localeCompare(b.path));
  return sortedFolders.reduce(insertFolderIfNotExist, { ...studiesTree });
}

/**
 * Insert a workspace into the study tree if it doesn't exist already.
 *
 * This function doesn't mutate the tree, it returns a new tree with the workspace inserted.
 *
 * @param workspace - key of the workspace
 * @param studyTree - study tree to insert the workspace into
 * @returns study tree with the empty workspace inserted if it wasn't already there.
 */
function insertWorkspaceIfNotExist(
  studyTree: StudyTreeNode,
  workspace: WorkspaceDTO,
): StudyTreeNode {
  const emptyNode = {
    name: workspace.name,
    path: `/${workspace.name}`,
    children: [],
    hasChildren: true,
    alias: workspace.disk_name,
  };
  console.log("insertWorkspaceIfNotExist", workspace, emptyNode);
  if (studyTree.children.some((child) => isNodeMatchWorkspace(child, workspace))) {
    return {
      ...studyTree,
      children: studyTree.children.map((child) => {
        if (isNodeMatchWorkspace(child, workspace)) {
          return { ...child, alias: workspace.disk_name };
        }
        return child;
      }),
    };
  }
  return {
    ...studyTree,
    children: [...studyTree.children, emptyNode],
  };
}

function isNodeMatchWorkspace(a: StudyTreeNode, b: WorkspaceDTO): boolean {
  return a.name === b.name;
}
/**
 * Insert several workspaces into the study tree if they don't exist already in the tree.
 *
 * This function doesn't mutate the tree, it returns a new tree with the workspaces inserted.
 *
 * The workspaces are inserted in the order they are given.
 *
 * @param workspaces - workspaces to insert into the tree
 * @param studyTree - study tree to insert the workspaces into
 * @returns study tree with the empty workspaces inserted if they weren't already there.
 */
export function insertWorkspacesIfNotExist(
  studyTree: StudyTreeNode,
  workspaces: WorkspaceDTO[],
): StudyTreeNode {
  return workspaces.reduce((acc, workspace) => insertWorkspaceIfNotExist(acc, workspace), {
    ...studyTree,
  });
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
 * Insert workspaces and folders into the study tree if they don't exist already.
 *
 * This function doesn't mutate the tree, it returns a new tree with the workspaces and folders inserted.
 *
 * @param studyTree - study tree to insert the workspaces and folders into
 * @param workspaces - workspaces to insert into the tree
 * @param folders - folders to insert into the tree
 * @returns study tree with the workspaces and folders inserted if they weren't already there.
 */
export function insertIfNotExist(
  studyTree: StudyTreeNode,
  workspaces: WorkspaceDTO[],
  folders: FolderDTO[],
) {
  const treeWithWorkspaces = insertWorkspacesIfNotExist(studyTree, workspaces);
  const treeWithFolders = insertFoldersIfNotExist(treeWithWorkspaces, folders);
  return treeWithFolders;
}

export function deleteStudyFromLocalStorage(event: StudyEventPayload) {
  const folders = storage.getItem(StorageKey.StudyTreeFolders) || [];
  const filteredFolders = folders.filter(
    (f) => !(f.workspace === event.workspace && f.path === event.folder),
  );
  storage.setItem(StorageKey.StudyTreeFolders, filteredFolders);
}
