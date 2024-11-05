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

import { StudyMetadata } from "@/common/types";

export interface StudyTreeNode {
  name: string;
  path: string;
  children: StudyTreeNode[];
}

const nodeProcess = (
  tree: StudyTreeNode,
  path: string[],
  folderPath: string,
): void => {
  const { children } = tree;
  if (path.length === 1) {
    return;
  }
  const element = path.pop() || "";
  const index = children.findIndex(
    (elm: StudyTreeNode) => elm.name === element,
  );
  const newFolderPath = `${folderPath}/${element}`;
  if (index < 0) {
    children.push({ name: element, children: [], path: newFolderPath });
    nodeProcess(
      children[children.length - 1] as StudyTreeNode,
      path,
      newFolderPath,
    );
  } else {
    nodeProcess(children[index] as StudyTreeNode, path, newFolderPath);
  }
};

export const buildStudyTree = (studies: StudyMetadata[]): StudyTreeNode => {
  const tree: StudyTreeNode = { name: "root", children: [], path: "" };
  let path: string[] = [];
  for (const study of studies) {
    if (study.folder !== undefined && study.folder !== null) {
      path = [
        study.workspace,
        ...(study.folder as string).split("/").filter((elm) => elm !== ""),
      ];
    } else {
      path = [study.workspace];
    }
    path.reverse();
    nodeProcess(tree, path, "");
  }
  return tree;
};
