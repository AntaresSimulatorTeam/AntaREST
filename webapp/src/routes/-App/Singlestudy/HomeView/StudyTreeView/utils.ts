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

/* eslint-disable no-param-reassign */
import type { GenericInfo, StudyMetadata, VariantTree } from "../../../../../types/types";

export interface StudyTree {
  name: string;
  attributes: {
    id: string;
  };
  drawOptions: {
    depth: number;
    nbAllChildrens: number;
  };
  children: StudyTree[];
}

const buildNodeFromMetadata = (study: StudyMetadata): StudyTree => ({
  name: study.name,
  attributes: {
    id: study.id,
  },
  drawOptions: {
    depth: 0,
    nbAllChildrens: 0,
  },
  children: [],
});

const convertVariantTreeToStudyTree = (tree: VariantTree): StudyTree => {
  const nodeDatum = buildNodeFromMetadata(tree.node);
  if (tree.children.length === 0) {
    nodeDatum.drawOptions.depth = 1;
    nodeDatum.drawOptions.nbAllChildrens = 0;
    nodeDatum.children = [];
  } else {
    nodeDatum.children = (tree.children || []).map((el: VariantTree) =>
      convertVariantTreeToStudyTree(el),
    );
    nodeDatum.drawOptions.depth =
      1 + Math.max(...nodeDatum.children.map((elm) => elm.drawOptions.depth));
    nodeDatum.drawOptions.nbAllChildrens = nodeDatum.children
      .map((elm) => 1 + elm.drawOptions.nbAllChildrens)
      .reduce((acc, curr) => acc + curr);
  }

  return nodeDatum;
};

const buildTree = async (node: StudyTree, childrenTree: VariantTree): Promise<void> => {
  if ((childrenTree.children || []).length === 0) {
    node.drawOptions.depth = 1;
    node.drawOptions.nbAllChildrens = 0;
    return;
  }
  const children = convertVariantTreeToStudyTree(childrenTree);
  node.drawOptions = children.drawOptions;
  node.children = children.children;
};

export const getTreeNodes = async (tree: VariantTree): Promise<StudyTree> => {
  const root = buildNodeFromMetadata(tree.node);
  await buildTree(root, tree);
  return root;
};

export const createListFromTree = (tree: StudyTree): GenericInfo[] => {
  const { name, attributes, children } = tree;
  const { id } = attributes;
  let res: GenericInfo[] = [{ id, name }];
  children.forEach((elm) => {
    res = res.concat(createListFromTree(elm));
  });
  return res;
};

export default {};
