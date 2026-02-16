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

import type { StudyMetadata, VariantTree } from "@/types/types";
import { COLORS } from "./constants";

export interface LayoutNode {
  name: string;
  attributes: {
    id: string;
  };
  drawOptions: {
    depth: number;
    totalDescendants: number;
  };
  children: LayoutNode[];
}

interface NodeColors {
  solid: string;
  faint: string;
  highlight: string;
  base: string;
  verticalLine: string;
}

function buildLeafNode(study: StudyMetadata): LayoutNode {
  return {
    name: study.name,
    attributes: { id: study.id },
    drawOptions: { depth: 1, totalDescendants: 0 },
    children: [],
  };
}

/**
 * Recursively converts a `VariantTree` into a `LayoutNode` that carries pre-computed layout metrics
 * (`depth` and `totalDescendants`) used for SVG rendering.
 *
 * @param tree - The variant tree node to convert.
 * @returns The corresponding `LayoutNode` with layout metrics.
 */
function toLayoutNode(tree: VariantTree): LayoutNode {
  if (tree.children.length === 0) {
    return buildLeafNode(tree.node);
  }

  const children = tree.children.map(toLayoutNode);
  const depth = 1 + Math.max(...children.map((c) => c.drawOptions.depth));
  const totalDescendants = children.reduce((sum, c) => sum + 1 + c.drawOptions.totalDescendants, 0);

  return {
    name: tree.node.name,
    attributes: { id: tree.node.id },
    drawOptions: { depth, totalDescendants },
    children,
  };
}

/**
 * Converts a variant tree returned by the API into a `LayoutNode`
 * ready for rendering in the SVG tree view.
 *
 * @param variantTree - The root variant tree from the API.
 * @returns A `LayoutNode` with pre-computed layout metrics for SVG rendering.
 */
export function buildLayoutTree(variantTree: VariantTree): LayoutNode {
  return toLayoutNode(variantTree);
}

export function getNodeColors(depth: number): NodeColors {
  const base = COLORS[depth % COLORS.length];

  return {
    solid: `${base}ff`,
    faint: `${base}0d`,
    highlight: `${base}44`,
    base,
    verticalLine: COLORS[(depth + 1) % COLORS.length],
  };
}

/**
 * Computes the starting row index for each direct child, accounting
 * for the vertical space consumed by preceding siblings and their
 * subtrees.
 *
 * @param children - Direct child nodes to compute rows for.
 * @param parentRow - The row index of the parent node.
 * @returns An array of row indices, one per child.
 */
export function computeChildRows(children: readonly LayoutNode[], parentRow: number): number[] {
  const rows: number[] = [];
  let currentRow = parentRow + 1;

  for (const child of children) {
    rows.push(currentRow);
    currentRow += child.drawOptions.totalDescendants + 1;
  }

  return rows;
}
