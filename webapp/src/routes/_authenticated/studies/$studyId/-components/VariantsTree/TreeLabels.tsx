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

import { Box } from "@mui/material";
import {
  DCY,
  RECT_DECORATION,
  RECT_Y_SPACING,
  RECT_Y_SPACING_2,
  TEXT_SIZE,
  TEXT_SPACING,
  TILE_SIZE_Y,
  TILE_SIZE_Y_2,
  ZOOM_OUT,
} from "./constants";
import { computeChildRows, getNodeColors, type LayoutNode } from "./utils";

interface TreeLabelsProps {
  node: LayoutNode;
  depth: number;
  row: number;
  hoverId: string | null;
  currentStudyId: string;
  isDarkMode: boolean;
  onClick: (studyId: string) => void;
  onHover: (id: string | null) => void;
}

function TreeLabels({
  node,
  depth,
  row,
  hoverId,
  currentStudyId,
  isDarkMode,
  onClick,
  onHover,
}: TreeLabelsProps) {
  const { name, attributes, children } = node;
  const { id } = attributes;
  const colors = getNodeColors(depth);
  const isActive = hoverId === id || currentStudyId === id;
  const childRows = computeChildRows(children, row);
  const cy = row * TILE_SIZE_Y + DCY;

  return (
    <>
      <Box
        component="button"
        type="button"
        title={name}
        aria-current={currentStudyId === id ? "page" : undefined}
        onClick={() => onClick(id)}
        onMouseEnter={() => onHover(id)}
        onMouseLeave={() => onHover(null)}
        sx={{
          // Use the SVG's row coordinates so both columns share one vertical scroll.
          position: "absolute",
          top: (cy - TILE_SIZE_Y_2 + RECT_Y_SPACING_2) / ZOOM_OUT,
          left: 0,
          width: 1,
          height: (TILE_SIZE_Y - RECT_Y_SPACING) / ZOOM_OUT,
          border: 0,
          borderLeft: `${RECT_DECORATION / ZOOM_OUT}px solid ${colors.base}`,
          px: `${TEXT_SPACING / ZOOM_OUT}px`,
          py: 0,
          bgcolor: isActive ? colors.base : colors.faint,
          color: isDarkMode && !isActive ? "white" : "black",
          fontFamily: "inherit",
          fontSize: TEXT_SIZE / ZOOM_OUT,
          textAlign: "left",
          whiteSpace: "nowrap",
          overflow: "hidden",
          textOverflow: "ellipsis",
          cursor: "pointer",
        }}
      >
        {name}
      </Box>
      {children.map((child, index) => (
        <TreeLabels
          key={child.attributes.id}
          node={child}
          depth={depth + 1}
          row={childRows[index]}
          hoverId={hoverId}
          currentStudyId={currentStudyId}
          isDarkMode={isDarkMode}
          onClick={onClick}
          onHover={onHover}
        />
      ))}
    </>
  );
}

export default TreeLabels;
