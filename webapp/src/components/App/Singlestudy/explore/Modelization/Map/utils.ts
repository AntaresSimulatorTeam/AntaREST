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

import { useMemo } from "react";
import type { StudyLayer } from "../../../../../../types/types";
import type { StudyMapNode } from "../../../../../../redux/ducks/studyMaps";

////////////////////////////////////////////////////////////////
// Types
////////////////////////////////////////////////////////////////

export type RGB = [number, number, number];

////////////////////////////////////////////////////////////////
// Constants
////////////////////////////////////////////////////////////////

export const NODE_HEIGHT = 400;
export const INITIAL_ZOOM = 0.8;
export const MAX_ZOOM_LEVEL = 8;
export const MIN_ZOOM_LEVEL = 0.1;
export const NODE_COLOR = "rgb(230, 108, 44)";

////////////////////////////////////////////////////////////////
// Utils
////////////////////////////////////////////////////////////////

export const getNodeWidth = (nodeText: string): number => {
  const fontSize = 16;
  const TEXT_SIZE = nodeText.length;

  if (TEXT_SIZE === 1) {
    return fontSize * TEXT_SIZE * 36;
  }
  if (TEXT_SIZE <= 2) {
    return fontSize * TEXT_SIZE * 20;
  }
  if (TEXT_SIZE <= 3) {
    return fontSize * TEXT_SIZE * 12;
  }
  if (TEXT_SIZE <= 5) {
    return fontSize * TEXT_SIZE * 10;
  }
  if (TEXT_SIZE <= 6) {
    return fontSize * TEXT_SIZE * 8.5;
  }
  if (TEXT_SIZE <= 10) {
    return fontSize * TEXT_SIZE * 7.5;
  }
  return fontSize * TEXT_SIZE * 6.5;
};

export function getUpdatedNode(id: string, nodeData: StudyMapNode[]): StudyMapNode | undefined {
  return nodeData.find((node) => node.id === id);
}

const getLuminanace = (values: RGB): number => {
  const rgb = values.map((v) => {
    const val = v / 255;
    return val <= 0.03928 ? val / 12.92 : ((val + 0.055) / 1.055) ** 2.4;
  });
  return Number((0.2126 * rgb[0] + 0.7152 * rgb[1] + 0.0722 * rgb[2]).toFixed(3));
};

const getContrastRatio = (colorA: RGB, colorB: RGB): number => {
  const lumA = getLuminanace(colorA);
  const lumB = getLuminanace(colorB);

  return (Math.max(lumA, lumB) + 0.05) / (Math.min(lumA, lumB) + 0.05);
};

export const getTextColor = (bgColor: RGB): string => {
  const whiteContrast = getContrastRatio(bgColor || [], [255, 255, 255]);
  const blackContrast = getContrastRatio(bgColor || [], [0, 0, 0]);

  return whiteContrast > blackContrast ? "#ffffff" : "#000000";
};

////////////////////////////////////////////////////////////////
// Hooks
////////////////////////////////////////////////////////////////

/**
 * Custom hook to compute and return nodes with adjusted positions based on the current layer and view settings.
 * It adjusts node positions to ensure they are correctly positioned in the graph based on the current zoom level and layer.
 * Additionally, it calculates the color for each node, supporting layer-specific color adjustments.
 *
 * @param nodes - Array of nodes to render.
 * @param width - Width of the rendering area.
 * @param height - Height of the rendering area.
 * @param currentLayerId - The ID of the current layer, used to adjust node positions and colors.
 * @returns Array of nodes with updated positions and colors for rendering.
 */
export function useRenderNodes(
  nodes: StudyMapNode[],
  width: number,
  height: number,
  currentLayerId: StudyLayer["id"],
): StudyMapNode[] {
  // compute center offset with scale fix on x axis
  const centerVector = { x: width / INITIAL_ZOOM / 2, y: height / 2 };
  // get real center from origin enclosing rectangle
  const realCenter = {
    y: 0,
    x: 0,
  };

  return useMemo(
    () =>
      nodes.map((node) => {
        const x = node.layerX[currentLayerId]
          ? node.layerX[currentLayerId] + centerVector.x - realCenter.x
          : node.x + centerVector.x - realCenter.x;
        const y = node.layerY[currentLayerId]
          ? -node.layerY[currentLayerId] + centerVector.y + realCenter.y
          : -node.y + centerVector.y + realCenter.y;
        const color = node.layerColor[currentLayerId]
          ? `rgb(${node.layerColor[currentLayerId]})`
          : NODE_COLOR;
        const rgbColor = node.layerColor[currentLayerId]
          ? node.layerColor[currentLayerId].split(",").map(Number)
          : NODE_COLOR.slice(4, -1).split(",").map(Number);
        return {
          ...node,
          x,
          y,
          color,
          rgbColor,
        };
      }),
    [currentLayerId, nodes, centerVector.x, realCenter.x, realCenter.y, centerVector.y],
  );
}
