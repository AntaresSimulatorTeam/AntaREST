import { useMemo } from "react";
import { StudyLayer } from "../../../../../../common/types";
import { StudyMapNode } from "../../../../../../redux/ducks/studyMaps";

////////////////////////////////////////////////////////////////
// Types
////////////////////////////////////////////////////////////////

export type RGB = [number, number, number];

////////////////////////////////////////////////////////////////
// Constants
////////////////////////////////////////////////////////////////

export const NODE_HEIGHT = 400;
export const INITIAL_ZOOM = 1;
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

export function getUpdatedNode(
  id: string,
  nodeData: StudyMapNode[]
): StudyMapNode | undefined {
  return nodeData.find((node) => node.id === id);
}

const getLuminanace = (values: RGB): number => {
  const rgb = values.map((v) => {
    const val = v / 255;
    return val <= 0.03928 ? val / 12.92 : ((val + 0.055) / 1.055) ** 2.4;
  });
  return Number(
    (0.2126 * rgb[0] + 0.7152 * rgb[1] + 0.0722 * rgb[2]).toFixed(3)
  );
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
 * Sets the graph nodes from the nodes data
 */
export function useRenderNodes(
  nodes: StudyMapNode[],
  width: number,
  height: number,
  currentLayerId: StudyLayer["id"]
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
    [
      currentLayerId,
      nodes,
      centerVector.x,
      realCenter.x,
      realCenter.y,
      centerVector.y,
    ]
  );
}
