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
import { ROOT_NODE_NAME } from "@/components/utils/constants";
import type { Directory } from "@/services/api/directories/types";
import type { DirectoryTreeNode } from "./types";

/**
 * Builds a hierarchical tree structure from a flat list of directories
 * using parentId relationships.
 *
 * @param directories - Flat array of Directory objects from the API
 * @returns Root DirectoryTreeNode with nested children
 *
 * @example
 * const directories = [
 *   { id: '1', name: 'Directory 1', parentId: null },
 *   { id: '2', name: 'Subdirectory', parentId: '1' }
 * ];
 * const tree = buildDirectoryTree(directories);
 * Returns: { name: 'Root', path: '', children: [{ name: 'Directory 1', ... }] }
 */
export function buildDirectoryTree(directories: Directory[]): DirectoryTreeNode {
  // const byId = R.indexBy(R.prop("id"), directories);

  // Find all root-level directories (those with parentId === null)
  const rootDirs = directories.filter((d) => d.parentId === null);

  const buildNode = (dir: Directory): DirectoryTreeNode => {
    const childDirs = directories.filter((d) => d.parentId === dir.id);
    const sortedChildren = R.sortBy(R.compose(R.toLower, R.prop("name")), childDirs);

    return {
      id: dir.id,
      name: dir.name,
      path: dir.id, // Use ID as path for selection/navigation
      parentId: dir.parentId,
      children: sortedChildren.map(buildNode),
    };
  };

  // Sort root directories by name
  const sortedRoots = R.sortBy(R.compose(R.toLower, R.prop("name")), rootDirs);

  // Return the root node with all top-level directories as children
  return {
    id: "",
    name: ROOT_NODE_NAME,
    path: "",
    parentId: null,
    children: sortedRoots.map(buildNode),
  };
}

/**
 * Flattens a directory tree into an array of all nodes
 * Useful for searching or filtering
 *
 * @param node - Root DirectoryTreeNode
 * @returns Flat array of all nodes in the tree
 */
export function flattenDirectoryTree(node: DirectoryTreeNode): DirectoryTreeNode[] {
  const flatten = (node: DirectoryTreeNode): DirectoryTreeNode[] => [
    node,
    ...R.chain(flatten, node.children),
  ];

  return flatten(node);
}

/**
 * Finds a directory node by its ID in the tree
 *
 * @param tree - Root DirectoryTreeNode
 * @param id - Directory ID to find
 * @returns DirectoryTreeNode or undefined if not found
 */
export function findDirectoryById(
  tree: DirectoryTreeNode,
  id: string,
): DirectoryTreeNode | undefined {
  const allNodes = flattenDirectoryTree(tree);
  return allNodes.find((node) => node.id === id);
}

/**
 * Gets all descendant IDs of a directory from a flat directory list,
 * including the directory itself.
 *
 * @param directoryId - The ID of the starting directory
 * @param directories - Flat array of all directories
 * @returns Array containing the given directoryId and all descendant IDs
 */
export function getDescendantIds(directoryId: string, directories: Directory[]): string[] {
  const children = directories.filter((directory) => directory.parentId === directoryId);
  return [directoryId, ...children.flatMap((child) => getDescendantIds(child.id, directories))];
}

/**
 * Gets the path from root to a specific directory node
 * Returns array of directory IDs representing the path
 *
 * @param tree - Root DirectoryTreeNode
 * @param targetId - ID of the target directory
 * @returns Array of directory IDs from root to target
 */
export function getDirectoryPath(tree: DirectoryTreeNode, targetId: string): string[] {
  const allNodes = flattenDirectoryTree(tree);
  const nodesById = R.indexBy(R.prop("id"), allNodes);

  const path: string[] = [];
  let currentId: string | null = targetId;

  while (currentId && nodesById[currentId]) {
    path.unshift(currentId);
    currentId = nodesById[currentId].parentId;
  }

  return path;
}
