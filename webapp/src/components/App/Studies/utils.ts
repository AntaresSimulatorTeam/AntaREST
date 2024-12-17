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

import { StudyMetadata } from "../../../common/types";

export interface StudyTreeNode {
  name: string;
  path: string;
  children: StudyTreeNode[];
}

export interface NonStudyFolderDTO {
  name: string;
  path: string;
  workspace: string;
  parentPath: string;
}

/**
 * Builds a tree structure from a list of study metadata.
 *
 * @param studies - Array of study metadata objects.
 * @returns A tree structure representing the studies.
 */
export function buildStudyTree(studies: StudyMetadata[]) {
  const tree: StudyTreeNode = { name: "root", children: [], path: "" };

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
          path: current.path ? `${current.path}/${folderName}` : folderName,
        };

        current.children.push(child);
      }

      current = child;
    }
  }

  return tree;
}
