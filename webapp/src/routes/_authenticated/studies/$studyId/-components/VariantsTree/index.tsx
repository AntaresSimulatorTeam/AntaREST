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

import useThemeColorScheme from "@/hooks/useThemeColorScheme";
import type { StudyMetadata, VariantTree } from "@/types/types";
import { Box, styled } from "@mui/material";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  CIRCLE_RADIUS,
  colors,
  CURVE_OFFSET,
  DCX,
  DCY,
  DEPTH_OFFSET,
  MIN_WIDTH,
  RECT_DECORATION,
  RECT_TEXT_WIDTH,
  RECT_X_SPACING,
  RECT_Y_SPACING,
  RECT_Y_SPACING_2,
  STROKE_WIDTH,
  TEXT_SIZE,
  TEXT_SPACING,
  TILE_SIZE_X,
  TILE_SIZE_Y,
  TILE_SIZE_Y_2,
  ZOOM_OUT,
} from "./treeconfig";
import { getTreeNodes, type StudyTree } from "./utils";

export const SVGCircle = styled("circle")({
  cursor: "pointer",
});
export const SVGRect = styled("rect")({
  cursor: "pointer",
});

export const SVGText = styled("text")({
  cursor: "pointer",
});

interface Props {
  study: StudyMetadata;
  variantTree: VariantTree;
  onClick: (studyId: string) => void;
}

export default function StudyTreeView({ study, variantTree, onClick }: Props) {
  const [studyTree, setStudyTree] = useState<StudyTree>();
  const [hoverId, setHoverId] = useState<string>("");
  const [containerWidth, setContainerWidth] = useState(0);
  const containerRef = useRef<HTMLDivElement>(null);
  const { isDarkMode } = useThemeColorScheme();

  // Track container width so we can expand the SVG to fill it
  useEffect(() => {
    const el = containerRef.current;
    if (!el) {
      return;
    }
    const observer = new ResizeObserver(([entry]) => {
      setContainerWidth(entry.contentRect.width);
    });
    observer.observe(el);
    return () => observer.disconnect();
  }, []);

  // Base rect width derived from tree depth (the "tree lines" area)
  const baseRectWidth = useMemo(() => {
    if (studyTree === undefined) {
      return 0;
    }
    const { drawOptions } = studyTree;
    const { depth } = drawOptions;
    return Math.max(TILE_SIZE_X * (depth + DEPTH_OFFSET), MIN_WIDTH);
  }, [studyTree]);

  const baseTreeWidth = baseRectWidth + RECT_TEXT_WIDTH + RECT_X_SPACING;

  const treeHeight = useMemo(() => {
    if (studyTree === undefined) {
      return 0;
    }
    const { drawOptions } = studyTree;
    const { nbAllChildrens } = drawOptions;
    return TILE_SIZE_Y * (nbAllChildrens + 1) + TILE_SIZE_Y_2;
  }, [studyTree]);

  // The viewBox width is chosen so that when the SVG scales uniformly
  // by 1/ZOOM_OUT, its pixel width equals the container width.
  // viewBoxWidth / ZOOM_OUT = containerWidth  =>  viewBoxWidth = containerWidth * ZOOM_OUT
  // We floor it at the natural tree width so it never clips content.
  const viewBoxWidth = useMemo(() => {
    if (containerWidth > 0) {
      return Math.max(baseTreeWidth, containerWidth * ZOOM_OUT);
    }
    return baseTreeWidth;
  }, [baseTreeWidth, containerWidth]);

  // The text label area expands to absorb extra horizontal space
  const effectiveTextWidth = viewBoxWidth - baseRectWidth - RECT_X_SPACING;

  const onMouseOver = useCallback((hId: string) => {
    setHoverId(hId);
  }, []);

  const onMouseOut = useCallback(() => {
    setHoverId("");
  }, []);

  const buildRecursiveTree = (tree: StudyTree, i = 0, j = 0): React.ReactNode[] => {
    const { drawOptions, name, attributes, children } = tree;
    const { id } = attributes;
    const { nbAllChildrens } = drawOptions;
    const hoverColor = colors[i % colors.length];
    const color = `${hoverColor}FF`;
    const rectColor = `${hoverColor}0D`;
    const rectHoverColor = `${hoverColor}44`;
    const verticalLineColor = `${colors[(i + 1) % colors.length]}`;
    let verticalLineEnd = 0;

    if (children.length > 0) {
      verticalLineEnd = nbAllChildrens - children[children.length - 1].drawOptions.nbAllChildrens;
      verticalLineEnd = (j + verticalLineEnd) * TILE_SIZE_Y + CIRCLE_RADIUS;
    }

    const cx = i * TILE_SIZE_X + DCX;
    const cy = j * TILE_SIZE_Y + DCY;
    let res: React.ReactNode[] = [
      <SVGCircle key={`circle-${i}-${j}`} cx={cx} cy={cy} r={CIRCLE_RADIUS} fill={color} />,
      <SVGRect
        key={`rect-${i}-${j}`}
        x="0"
        y={cy - TILE_SIZE_Y_2 + RECT_Y_SPACING_2}
        width={baseRectWidth}
        height={TILE_SIZE_Y - RECT_Y_SPACING}
        fill={hoverId === id || study.id === id ? rectHoverColor : rectColor}
        onClick={() => onClick(id)}
        onMouseOver={() => onMouseOver(id)}
        onMouseOut={onMouseOut}
      />,
      <SVGRect
        key={`rect-for-name-${i}-${j}`}
        x={baseRectWidth + RECT_X_SPACING}
        y={cy - TILE_SIZE_Y_2 + RECT_Y_SPACING_2}
        width={effectiveTextWidth}
        height={TILE_SIZE_Y - RECT_Y_SPACING}
        fill={hoverId === id || study.id === id ? hoverColor : rectColor}
        onClick={() => onClick(id)}
        onMouseOver={() => onMouseOver(id)}
        onMouseOut={onMouseOut}
      />,
      <SVGRect
        key={`rect-for-name-deco-${i}-${j}`}
        x={baseRectWidth + RECT_X_SPACING}
        y={cy - TILE_SIZE_Y_2 + RECT_Y_SPACING_2}
        width={RECT_DECORATION}
        height={TILE_SIZE_Y - RECT_Y_SPACING}
        fill={hoverColor}
      />,
      <SVGText
        key={`name-${i}-${j}`}
        x={baseRectWidth + RECT_X_SPACING + RECT_DECORATION + TEXT_SPACING}
        y={cy + RECT_Y_SPACING_2}
        fill={isDarkMode ? (hoverId === id || study.id === id ? "black" : "white") : "black"}
        fontSize={TEXT_SIZE}
        onClick={() => onClick(id)}
        onMouseOver={() => onMouseOver(id)}
      >
        {name}
      </SVGText>,
    ];
    if (verticalLineEnd > 0) {
      res.push(
        <path
          key={`verticalLine-${i}-${j}`}
          d={`M ${cx} ${cy + CIRCLE_RADIUS} L ${cx} ${verticalLineEnd}`}
          fill={verticalLineColor}
          stroke={verticalLineColor}
          strokeWidth={`${STROKE_WIDTH}`}
        />,
      );
    }
    if (i > 0) {
      res.push(
        <path
          key={`horizontalLine-${i}-${j}`}
          d={`M ${cx - CIRCLE_RADIUS - CURVE_OFFSET},${cy} C ${
            cx - TILE_SIZE_X
          },${cy} ${cx - TILE_SIZE_X},${cy} ${cx - TILE_SIZE_X},${
            cy - TILE_SIZE_Y + 2 * CIRCLE_RADIUS
          } M ${cx - CIRCLE_RADIUS},${cy} L ${cx - CIRCLE_RADIUS - CURVE_OFFSET},${cy}`}
          fill="transparent"
          stroke={color}
          strokeWidth={`${STROKE_WIDTH}`}
        />,
      );
    }

    let recursiveHeight = 1;
    res = res.concat(
      children.map((elm, index) => {
        if (index === 0) {
          recursiveHeight = j + 1;
        } else {
          recursiveHeight = recursiveHeight + children[index - 1].drawOptions.nbAllChildrens + 1;
        }
        return buildRecursiveTree(elm, i + 1, recursiveHeight);
      }),
    );
    return res;
  };

  const renderTree = (tree: StudyTree): React.ReactNode => {
    return (
      <svg
        width="100%"
        height={treeHeight / ZOOM_OUT}
        preserveAspectRatio="xMinYMin meet"
        viewBox={`0 0 ${viewBoxWidth} ${treeHeight}`}
      >
        {buildRecursiveTree(tree, 0, 0)}
      </svg>
    );
  };

  useEffect(() => {
    const buildStudyTree = async () => {
      const tmp = await getTreeNodes(variantTree);
      setStudyTree(tmp);
    };

    buildStudyTree();
  }, [variantTree]);

  return (
    <Box
      ref={containerRef}
      display="flex"
      flexDirection="column"
      justifyContent="flex-start"
      alignItems="flex-start"
      sx={{
        width: "100%",
        flexGrow: 1,
        overflowY: "auto",
      }}
    >
      <Box
        width="100%"
        minWidth={baseTreeWidth / ZOOM_OUT}
        minHeight={treeHeight / ZOOM_OUT}
        display="flex"
        flexDirection="column"
        justifyContent="flex-start"
        alignItems="flex-start"
      >
        {studyTree && renderTree(studyTree)}
      </Box>
    </Box>
  );
}
