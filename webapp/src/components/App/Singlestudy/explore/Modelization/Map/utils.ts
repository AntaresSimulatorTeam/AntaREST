import { useEffect } from "react";
import { LinkProperties, NodeProperties } from "../../../../../../common/types";
import { setCurrentArea } from "../../../../../../redux/ducks/studySyntheses";
import useAppDispatch from "../../../../../../redux/hooks/useAppDispatch";

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

// TODO rework
export const getNodeWidth = (nodeText: string): number => {
  const FONT_SIZE = 16;
  const TEXT_SIZE = nodeText.length;

  if (TEXT_SIZE === 1) {
    return FONT_SIZE * TEXT_SIZE * 36;
  }
  if (TEXT_SIZE <= 2) {
    return FONT_SIZE * TEXT_SIZE * 20;
  }
  if (TEXT_SIZE <= 3) {
    return FONT_SIZE * TEXT_SIZE * 12;
  }
  if (TEXT_SIZE <= 5) {
    return FONT_SIZE * TEXT_SIZE * 10;
  }
  if (TEXT_SIZE <= 6) {
    return FONT_SIZE * TEXT_SIZE * 8.5;
  }
  if (TEXT_SIZE <= 10) {
    return FONT_SIZE * TEXT_SIZE * 7.5;
  }
  return FONT_SIZE * TEXT_SIZE * 6.5;
};

export function getUpdatedNode(
  id: string,
  nodeData: NodeProperties[]
): NodeProperties | undefined {
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
  const whiteContrast = getContrastRatio(bgColor, [255, 255, 255]);
  const blackContrast = getContrastRatio(bgColor, [0, 0, 0]);

  return whiteContrast > blackContrast ? "#ffffff" : "#000000";
};

////////////////////////////////////////////////////////////////
// Hooks
////////////////////////////////////////////////////////////////

/**
 * When a node is clicked sets the current selected node
 */
export function useSetCurrentNode(
  selectedNode: NodeProperties | undefined
): void {
  const dispatch = useAppDispatch();

  useEffect(() => {
    if (selectedNode) {
      // dispatch(setSelectedLink(undefined));
      dispatch(setCurrentArea(selectedNode.id));
    }
  }, [dispatch, selectedNode]);
}

/**
 * When a node is clicked sets the links for this node
 */
export function useSetSelectedNodeLinks(
  selectedNode: NodeProperties | undefined,
  mapLinks: LinkProperties[]
): void {
  const dispatch = useAppDispatch();

  useEffect(() => {
    if (selectedNode) {
      const nodeLinks = mapLinks.filter(
        (link) =>
          link.source === selectedNode.id || link.target === selectedNode.id
      );
      dispatch(setSelectedNodeLinks(nodeLinks));
    }
  }, [selectedNode, mapLinks, dispatch]);
}

/**
 * Sets the graph nodes from the nodes data
 */
export function useRenderNodes(
  nodes: NodeProperties[],
  width: number,
  height: number
): NodeProperties[] {
  // compute center offset with scale fix on x axis
  const centerVector = { x: width / INITIAL_ZOOM / 2, y: height / 2 };
  // get real center from origin enclosing rectangle
  const realCenter = {
    y: 0,
    x: 0,
  };
  // apply translations (y axis is inverted)
  const renderNodes = nodes.map((node) => ({
    ...node,
    x: node.x + centerVector.x - realCenter.x,
    y: -node.y + centerVector.y + realCenter.y,
  }));

  return renderNodes;
}
