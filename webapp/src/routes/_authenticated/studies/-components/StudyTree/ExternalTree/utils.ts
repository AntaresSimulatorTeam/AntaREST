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

import * as R from "ramda";
import { DEFAULT_WORKSPACE_NAME, ROOT_NODE_NAME } from "@/components/utils/constants";
import type { FolderDTO, WorkspaceDTO } from "@/queries/explorer/schemas";
import type { StudyMetadata } from "@/types/types";
import type { ExternalTreeNodeMetadata } from "./types";

// Builds the full path from a parent path and folder name
const buildPath = (parentPath: string, folderName: string): string =>
  parentPath ? `${parentPath}/${folderName}` : `/${folderName}`;

// Parses study metadata into path components
const parseStudyPath = (study: StudyMetadata): string[] => {
  const folderParts =
    typeof study.folder === "string" ? study.folder.split("/").filter(Boolean) : [];
  return [study.workspace, ...folderParts];
};

// Creates a study folder node (leaf node marked as scanned)
const createStudyFolderNode = (name: string, path: string): ExternalTreeNodeMetadata => ({
  name,
  children: [],
  path,
  isScannedStudy: true,
});

// Creates a regular folder node
const createFolderNode = (name: string, path: string): ExternalTreeNodeMetadata => ({
  name,
  children: [],
  path,
});

// Finds a child node by name
const findChildByName = (name: string) => R.find<ExternalTreeNodeMetadata>(R.propEq(name, "name"));

/**
 * Builds a tree structure from a list of study metadata.
 *
 * Note: Excludes the "default" workspace - managed studies are shown in ManagedTree.
 *
 * @param studies - Array of study metadata objects.
 * @returns A tree structure representing the studies.
 */
export const buildExternalTree = (studies: StudyMetadata[]): ExternalTreeNodeMetadata => {
  const initialTree: ExternalTreeNodeMetadata = {
    name: ROOT_NODE_NAME,
    children: [],
    path: "",
  };

  // Build tree iteratively
  return R.reduce(
    (tree, study) => {
      const pathComponents = parseStudyPath(study);
      let current = tree;

      for (let i = 0; i < pathComponents.length; i++) {
        const folderName = pathComponents[i];
        const isLastComponent = i === pathComponents.length - 1;

        if (isLastComponent) {
          // Add study folder with isScannedStudy flag
          const studyPath = buildPath(current.path, folderName);
          const studyNode = createStudyFolderNode(folderName, studyPath);
          current.children.push(studyNode);
          break;
        }

        // Find or create intermediate folder
        let child = findChildByName(folderName)(current.children);

        if (!child) {
          child = createFolderNode(folderName, buildPath(current.path, folderName));
          current.children.push(child);
        }

        current = child;
      }

      return tree;
    },
    initialTree,
    studies,
  );
};

// Check if a folder path starts with a given prefix
const pathStartsWith =
  (prefix: string) =>
  (folderPath: string): boolean =>
    folderPath.startsWith(prefix);

// Updates or adds a folder node with new metadata
const updateOrAddFolder = (
  children: ExternalTreeNodeMetadata[],
  folder: FolderDTO,
  parentPath: string,
): ExternalTreeNodeMetadata[] => {
  const existingFolder = findChildByName(folder.name)(children);

  if (existingFolder) {
    // Update existing folder with new metadata
    return children.map((child) =>
      child.name === folder.name
        ? {
            ...child,
            hasChildren: folder.hasChildren,
            isStudyFolder: folder.isStudyFolder,
          }
        : child,
    );
  }

  // Add new folder
  const newFolder: ExternalTreeNodeMetadata = {
    path: `${parentPath}/${folder.name}`,
    name: folder.name,
    children: [],
    hasChildren: folder.hasChildren,
    isStudyFolder: folder.isStudyFolder,
  };

  return [...children, newFolder];
};

/**
 * Add a folder that was returned by the explorer into the external tree view.
 *
 * This function doesn't mutate the tree, it returns a new tree with the folder inserted.
 * If the folder is already in the tree, the tree returned will be equal to the tree given to the function.
 *
 * @param tree - external tree to insert the folder into
 * @param folder - folder to insert into the tree
 * @returns external tree with the folder inserted if it wasn't already there.
 */
const insertFolderIfNotExist = (
  tree: ExternalTreeNodeMetadata,
  folder: FolderDTO,
): ExternalTreeNodeMetadata => {
  const currentNodePath = tree.path;

  // Early return if folder doesn't belong in this branch
  if (!pathStartsWith(currentNodePath)(folder.parentPath)) {
    return tree;
  }

  // Direct child case
  if (folder.parentPath === currentNodePath) {
    return {
      ...tree,
      children: updateOrAddFolder(tree.children, folder, currentNodePath),
    };
  }

  // Not a direct child, recursively walk through the tree
  return {
    ...tree,
    children: R.map((child) => insertFolderIfNotExist(child, folder), tree.children),
  };
};

/**
 * Sorts folders by path for consistent insertion order
 */
const sortByPath = R.sortBy<FolderDTO>(R.prop("path"));

/**
 * Insert several folders in the external tree if they don't exist already in the tree.
 *
 * This function doesn't mutate the tree, it returns a new tree with the folders inserted.
 *
 * @param tree - external tree to insert the folder into
 * @param folders - folders to insert into the tree
 * @returns external tree with the folder inserted if it wasn't already there.
 */
export const insertFoldersIfNotExist = (
  tree: ExternalTreeNodeMetadata,
  folders: FolderDTO[],
): ExternalTreeNodeMetadata => {
  const sortedFolders = sortByPath(folders);
  return R.reduce((acc, folder) => insertFolderIfNotExist(acc, folder), tree, sortedFolders);
};

// Creates an empty workspace node
const createWorkspaceNode = (workspace: WorkspaceDTO): ExternalTreeNodeMetadata => ({
  name: workspace.name,
  path: `/${workspace.name}`,
  children: [],
  hasChildren: true,
  alias: workspace.diskName,
});

// Checks if a node matches a workspace
const isNodeMatchWorkspace = (node: ExternalTreeNodeMetadata, workspace: WorkspaceDTO): boolean =>
  node.name === workspace.name;

// Adds workspace alias to matching node
const addWorkspaceAlias = (workspace: WorkspaceDTO) =>
  R.when<ExternalTreeNodeMetadata, ExternalTreeNodeMetadata>(
    (node) => isNodeMatchWorkspace(node, workspace),
    R.assoc("alias", workspace.diskName),
  );

/**
 * Insert a workspace into the external tree if it doesn't exist already.
 * Filters out "default" workspace - managed studies are shown in ManagedTree.
 *
 * @param tree - external tree to insert the workspace into
 * @param workspace - workspace to insert
 * @returns external tree with the workspace inserted if it wasn't already there.
 */
const insertWorkspaceIfNotExist = (
  tree: ExternalTreeNodeMetadata,
  workspace: WorkspaceDTO,
): ExternalTreeNodeMetadata => {
  if (workspace.name === DEFAULT_WORKSPACE_NAME) {
    return tree;
  }

  const hasWorkspace = R.any((child) => isNodeMatchWorkspace(child, workspace), tree.children);

  if (hasWorkspace) {
    return {
      ...tree,
      children: R.map(addWorkspaceAlias(workspace), tree.children),
    };
  }

  return {
    ...tree,
    children: [...tree.children, createWorkspaceNode(workspace)],
  };
};

/**
 * Insert several workspaces into the external tree if they don't exist already in the tree.
 *
 * @param tree - external tree to insert the workspaces into
 * @param workspaces - workspaces to insert into the tree
 * @returns external tree with the empty workspaces inserted if they weren't already there.
 */
export const insertWorkspacesIfNotExist = (
  tree: ExternalTreeNodeMetadata,
  workspaces: WorkspaceDTO[],
): ExternalTreeNodeMetadata =>
  R.reduce((acc, workspace) => insertWorkspaceIfNotExist(acc, workspace), tree, workspaces);

/**
 * Insert workspaces and folders into the external tree if they don't exist already.
 *
 * @param tree - external tree to insert the workspaces and folders into
 * @param workspaces - workspaces to insert into the tree
 * @param folders - folders to insert into the tree
 * @returns external tree with the workspaces and folders inserted if they weren't already there.
 */
export const insertIfNotExist = (
  tree: ExternalTreeNodeMetadata,
  workspaces: WorkspaceDTO[],
  folders: FolderDTO[],
): ExternalTreeNodeMetadata =>
  R.pipe(
    (t: ExternalTreeNodeMetadata) => insertWorkspacesIfNotExist(t, workspaces),
    (t: ExternalTreeNodeMetadata) => insertFoldersIfNotExist(t, folders),
  )(tree);

/**
 * Checks if a folder represents an unscanned study
 * (i.e., a study folder that exists but hasn't been scanned into the database yet)
 *
 * @param studies - studies to check against
 * @param folder - folder to check
 * @returns true if the folder represents an unscanned study, false otherwise
 */
export const isUnscannedStudy = (studies: StudyMetadata[], folder: FolderDTO): boolean =>
  !R.any((study) => folder.path === study.folder && study.workspace === folder.workspace, studies);
