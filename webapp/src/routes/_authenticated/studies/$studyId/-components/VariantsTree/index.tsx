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

import CustomScrollbar from "@/components/CustomScrollbar";
import useThemeColorScheme from "@/hooks/useThemeColorScheme";
import type { VariantTree } from "@/services/api/studies/variants/types";
import { measureTextWidth } from "@/utils/domUtils";
import { Box, useTheme } from "@mui/material";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import useStudy from "../../-hooks/useStudy";
import {
  DEPTH_OFFSET,
  MIN_WIDTH,
  RECT_DECORATION,
  RECT_TEXT_WIDTH,
  RECT_X_SPACING,
  TEXT_SIZE,
  TEXT_SPACING,
  TILE_SIZE_X,
  TILE_SIZE_Y,
  TILE_SIZE_Y_2,
  ZOOM_OUT,
} from "./constants";
import TreeNode from "./TreeNode";
import TreeLabels from "./TreeLabels";
import { buildLayoutTree, type LayoutNode } from "./utils";

interface VariantsTreeProps {
  variantTree: VariantTree;
  onClick: (studyId: string) => void;
}

function VariantsTree({ variantTree, onClick }: VariantsTreeProps) {
  const [hoverId, setHoverId] = useState<string | null>(null);
  const [containerWidth, setContainerWidth] = useState(0);
  const containerRef = useRef<HTMLDivElement>(null);
  const { typography } = useTheme();
  const { isDarkMode } = useThemeColorScheme();
  const layoutTree = useMemo(() => buildLayoutTree(variantTree), [variantTree]);
  const { depth, totalDescendants } = layoutTree.drawOptions;
  const study = useStudy();

  const defaultLabelWidth = useMemo(() => {
    const font = `${TEXT_SIZE / ZOOM_OUT}px ${typography.fontFamily}`;

    function getMaxTextWidth({ name, children }: LayoutNode): number {
      return Math.max(measureTextWidth(name, font), ...children.map(getMaxTextWidth));
    }

    const textWidth = getMaxTextWidth(layoutTree);
    return textWidth > 0
      ? Math.ceil(textWidth + (RECT_DECORATION + 2 * TEXT_SPACING) / ZOOM_OUT)
      : RECT_TEXT_WIDTH / ZOOM_OUT;
  }, [layoutTree, typography.fontFamily]);

  useEffect(() => {
    const element = containerRef.current;
    if (!element) {
      return;
    }

    const observer = new ResizeObserver(([entry]) => {
      setContainerWidth(entry.contentRect.width);
    });

    observer.observe(element);
    return () => observer.disconnect();
  }, []);

  const baseRectWidth = Math.max(TILE_SIZE_X * (depth + DEPTH_OFFSET), MIN_WIDTH);
  const treeHeight = TILE_SIZE_Y * (totalDescendants + 1) + TILE_SIZE_Y_2;

  // Size the label column to the widest title, up to half the panel width.
  // The graph uses the remaining space.
  const labelWidth =
    containerWidth > 0 ? Math.min(defaultLabelWidth, containerWidth / 2) : defaultLabelWidth;
  const graphWidth = Math.max(
    baseRectWidth,
    (containerWidth - labelWidth) * ZOOM_OUT - RECT_X_SPACING,
  );

  const handleHover = useCallback((id: string | null) => setHoverId(id), []);

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <Box
      ref={containerRef}
      sx={{
        width: 1,
        minWidth: 0,
        flexGrow: 1,
        overflow: "hidden",
      }}
    >
      <CustomScrollbar style={{ height: "100%" }}>
        <Box
          sx={{
            width: "max-content",
            minWidth: "100%",
            display: "flex",
            alignItems: "flex-start",
            gap: `${RECT_X_SPACING / ZOOM_OUT}px`,
          }}
        >
          <Box
            sx={{
              position: "sticky",
              left: 0,
              zIndex: 1,
              flexShrink: 0,
              width: labelWidth,
              height: treeHeight / ZOOM_OUT,
              bgcolor: "background.default",
            }}
          >
            <TreeLabels
              node={layoutTree}
              depth={0}
              row={0}
              hoverId={hoverId}
              currentStudyId={study.id}
              isDarkMode={isDarkMode}
              onClick={onClick}
              onHover={handleHover}
            />
          </Box>
          <svg
            role="img"
            aria-labelledby="variants-tree-title"
            width={graphWidth / ZOOM_OUT}
            height={treeHeight / ZOOM_OUT}
            preserveAspectRatio="xMinYMin meet"
            viewBox={`0 0 ${graphWidth} ${treeHeight}`}
          >
            <title id="variants-tree-title">Study variant tree</title>
            <TreeNode
              node={layoutTree}
              depth={0}
              row={0}
              baseRectWidth={graphWidth}
              hoverId={hoverId}
              currentStudyId={study.id}
              onClick={onClick}
              onHover={handleHover}
            />
          </svg>
        </Box>
      </CustomScrollbar>
    </Box>
  );
}

export default VariantsTree;
