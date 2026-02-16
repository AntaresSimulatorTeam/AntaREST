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

import { styled } from "@mui/material";
import {
  CIRCLE_RADIUS,
  CURVE_OFFSET,
  DCX,
  DCY,
  RECT_DECORATION,
  RECT_X_SPACING,
  RECT_Y_SPACING,
  RECT_Y_SPACING_2,
  STROKE_WIDTH,
  TEXT_SIZE,
  TEXT_SPACING,
  TILE_SIZE_X,
  TILE_SIZE_Y,
  TILE_SIZE_Y_2,
} from "./constants";
import { computeChildRows, getNodeColors, type LayoutNode } from "./utils";

const ClickableCircle = styled("circle")({ cursor: "pointer" });
const ClickableRect = styled("rect")({ cursor: "pointer" });
const ClickableText = styled("text")({ cursor: "pointer" });

interface TreeNodeProps {
  node: LayoutNode;
  depth: number;
  row: number;
  baseRectWidth: number;
  effectiveTextWidth: number;
  hoverId: string | null;
  currentStudyId: string;
  isDarkMode: boolean;
  onClick: (studyId: string) => void;
  onHover: (id: string | null) => void;
}

function TreeNode({
  node,
  depth,
  row,
  baseRectWidth,
  effectiveTextWidth,
  hoverId,
  currentStudyId,
  isDarkMode,
  onClick,
  onHover,
}: TreeNodeProps) {
  const { name, attributes, children, drawOptions } = node;
  const { id } = attributes;
  const { totalDescendants } = drawOptions;
  const colors = getNodeColors(depth);
  const isActive = hoverId === id || currentStudyId === id;
  const textFill = isDarkMode ? (isActive ? "black" : "white") : "black";
  const childRows = computeChildRows(children, row);

  // Circle centre coordinates
  const cx = depth * TILE_SIZE_X + DCX;
  const cy = row * TILE_SIZE_Y + DCY;

  // Row-highlight rectangle geometry
  const rectY = cy - TILE_SIZE_Y_2 + RECT_Y_SPACING_2;
  const rectHeight = TILE_SIZE_Y - RECT_Y_SPACING;

  // Vertical line from this node's circle down to the last child's connector curve.
  let verticalLineEndY = 0;

  if (children.length > 0) {
    const lastChild = children[children.length - 1];
    const lastChildRow = totalDescendants - lastChild.drawOptions.totalDescendants;
    verticalLineEndY = (row + lastChildRow) * TILE_SIZE_Y + CIRCLE_RADIUS;
  }

  const handleClick = () => onClick(id);
  const handleMouseOver = () => onHover(id);
  const handleMouseOut = () => onHover(null);

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <g>
      {/* Node circle  */}
      <ClickableCircle cx={cx} cy={cy} r={CIRCLE_RADIUS} fill={colors.solid} />

      {/* Row background (tree-lines area) */}
      <ClickableRect
        x={0}
        y={rectY}
        width={baseRectWidth}
        height={rectHeight}
        fill={isActive ? colors.highlight : colors.faint}
        onClick={handleClick}
        onMouseOver={handleMouseOver}
        onMouseOut={handleMouseOut}
      />

      {/* Label background */}
      <ClickableRect
        x={baseRectWidth + RECT_X_SPACING}
        y={rectY}
        width={effectiveTextWidth}
        height={rectHeight}
        fill={isActive ? colors.base : colors.faint}
        onClick={handleClick}
        onMouseOver={handleMouseOver}
        onMouseOut={handleMouseOut}
      />

      {/* Label accent bar */}
      <rect
        x={baseRectWidth + RECT_X_SPACING}
        y={rectY}
        width={RECT_DECORATION}
        height={rectHeight}
        fill={colors.base}
      />

      {/* Label text */}
      <ClickableText
        x={baseRectWidth + RECT_X_SPACING + RECT_DECORATION + TEXT_SPACING}
        y={cy + RECT_Y_SPACING_2}
        fill={textFill}
        fontSize={TEXT_SIZE}
        onClick={handleClick}
        onMouseOver={handleMouseOver}
      >
        {name}
      </ClickableText>

      {/* Vertical line to children */}
      {verticalLineEndY > 0 && (
        <path
          d={`M ${cx} ${cy + CIRCLE_RADIUS} L ${cx} ${verticalLineEndY}`}
          fill="none"
          stroke={colors.verticalLine}
          strokeWidth={STROKE_WIDTH}
        />
      )}

      {/* Curved connector back to parent */}
      {depth > 0 && (
        <path
          d={[
            `M ${cx - CIRCLE_RADIUS - CURVE_OFFSET},${cy}`,
            `C ${cx - TILE_SIZE_X},${cy}`,
            `  ${cx - TILE_SIZE_X},${cy}`,
            `  ${cx - TILE_SIZE_X},${cy - TILE_SIZE_Y + 2 * CIRCLE_RADIUS}`,
            `M ${cx - CIRCLE_RADIUS},${cy}`,
            `L ${cx - CIRCLE_RADIUS - CURVE_OFFSET},${cy}`,
          ].join(" ")}
          fill="transparent"
          stroke={colors.solid}
          strokeWidth={STROKE_WIDTH}
        />
      )}

      {children.map((child, index) => (
        <TreeNode
          key={child.attributes.id}
          node={child}
          depth={depth + 1}
          row={childRows[index]}
          baseRectWidth={baseRectWidth}
          effectiveTextWidth={effectiveTextWidth}
          hoverId={hoverId}
          currentStudyId={currentStudyId}
          isDarkMode={isDarkMode}
          onClick={onClick}
          onHover={onHover}
        />
      ))}
    </g>
  );
}

export default TreeNode;
