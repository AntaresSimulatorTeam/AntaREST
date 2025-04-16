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

import type { StudyMetadata } from "../../../../types/types";
import type { NonStudyFolderDTO, StudyTreeNode } from "./types";

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
  return folders.reduce(insertFolderIfNotExist, studiesTree);
}
