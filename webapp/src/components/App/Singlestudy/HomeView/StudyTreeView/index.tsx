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

import { useEffect, useMemo, useState } from "react";
import { Box, styled } from "@mui/material";
import type { StudyMetadata, VariantTree } from "../../../../../types/types";
import { getTreeNodes, type StudyTree } from "./utils";
import {
  CIRCLE_RADIUS,
  colors,
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
  CURVE_OFFSET,
} from "./treeconfig";
import useThemeColorScheme from "@/hooks/useThemeColorScheme";

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
  study: StudyMetadata | undefined;
  tree: VariantTree | undefined;
  onClick: (studyId: string) => void;
}

export default function CustomizedTreeView(props: Props) {
  const { study, tree, onClick } = props;
  const [studyTree, setStudyTree] = useState<StudyTree>();
  const [hoverId, setHoverId] = useState<string>("");
  const { isDarkMode } = useThemeColorScheme();

  const rectWidth = useMemo(() => {
    if (studyTree === undefined) {
      return 0;
    }
    const { drawOptions } = studyTree;
    const { depth } = drawOptions;
    return Math.max(TILE_SIZE_X * (depth + DEPTH_OFFSET), MIN_WIDTH);
  }, [studyTree]);

  const treeWidth = rectWidth + RECT_TEXT_WIDTH + RECT_X_SPACING;

  const treeHeight = useMemo(() => {
    if (studyTree === undefined) {
      return 0;
    }
    const { drawOptions } = studyTree;
    const { nbAllChildrens } = drawOptions;
    return TILE_SIZE_Y * (nbAllChildrens + 1) + TILE_SIZE_Y_2;
  }, [studyTree]);

  const onMouseOver = (hId: string) => {
    setHoverId(hId);
  };

  const onMouseOut = () => {
    setHoverId("");
  };

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
        width={rectWidth}
        height={TILE_SIZE_Y - RECT_Y_SPACING}
        fill={hoverId === id || study?.id === id ? rectHoverColor : rectColor}
        onClick={() => onClick(id)}
        onMouseOver={(e) => onMouseOver(id)}
        onMouseOut={onMouseOut}
      />,
      <SVGRect
        key={`rect-for-name-${i}-${j}`}
        x={rectWidth + RECT_X_SPACING}
        y={cy - TILE_SIZE_Y_2 + RECT_Y_SPACING_2}
        width={RECT_TEXT_WIDTH}
        height={TILE_SIZE_Y - RECT_Y_SPACING}
        fill={hoverId === id || study?.id === id ? hoverColor : rectColor}
        onClick={() => onClick(id)}
        onMouseOver={(e) => onMouseOver(id)}
        onMouseOut={onMouseOut}
      />,
      <SVGRect
        key={`rect-for-name-deco-${i}-${j}`}
        x={rectWidth + RECT_X_SPACING}
        y={cy - TILE_SIZE_Y_2 + RECT_Y_SPACING_2}
        width={RECT_DECORATION}
        height={TILE_SIZE_Y - RECT_Y_SPACING}
        fill={hoverColor}
      />,
      <SVGText
        key={`name-${i}-${j}`}
        x={rectWidth + RECT_X_SPACING + RECT_DECORATION + TEXT_SPACING}
        y={cy + RECT_Y_SPACING_2}
        fill={isDarkMode ? (hoverId === id || study?.id === id ? "black" : "white") : "black"}
        fontSize={TEXT_SIZE}
        onClick={() => onClick(id)}
        onMouseOver={(e) => onMouseOver(id)}
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
    const { drawOptions } = tree;
    const { depth, nbAllChildrens } = drawOptions;
    return (
      <svg
        viewBox={`0 0 ${
          Math.max(TILE_SIZE_X * (depth + DEPTH_OFFSET), MIN_WIDTH) +
          RECT_TEXT_WIDTH +
          RECT_X_SPACING
        } ${TILE_SIZE_Y * (nbAllChildrens + 1) + TILE_SIZE_Y_2}`}
      >
        {buildRecursiveTree(tree, 0, 0)}
      </svg>
    );
  };

  useEffect(() => {
    const buildStudyTree = async () => {
      if (study && tree) {
        const tmp = await getTreeNodes(tree);
        setStudyTree(tmp);
      }
    };
    buildStudyTree();
  }, [study, tree]);

  return (
    <Box
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
        minWidth={treeWidth / ZOOM_OUT}
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
