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
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import useThemeColorScheme from "@/hooks/useThemeColorScheme";
import type { StudyMetadata, VariantTree } from "@/types/types";
import {
  DEPTH_OFFSET,
  MIN_WIDTH,
  RECT_TEXT_WIDTH,
  RECT_X_SPACING,
  TILE_SIZE_X,
  TILE_SIZE_Y,
  TILE_SIZE_Y_2,
  ZOOM_OUT,
} from "./constants";
import TreeNode from "./TreeNode";
import { buildLayoutTree } from "./utils";

interface VariantsTreeProps {
  study: StudyMetadata;
  variantTree: VariantTree;
  onClick: (studyId: string) => void;
}

function VariantsTree({ study, variantTree, onClick }: VariantsTreeProps) {
  const [hoverId, setHoverId] = useState<string | null>(null);
  const [containerWidth, setContainerWidth] = useState(0);
  const containerRef = useRef<HTMLDivElement>(null);
  const { isDarkMode } = useThemeColorScheme();
  const layoutTree = useMemo(() => buildLayoutTree(variantTree), [variantTree]);
  const { depth, totalDescendants } = layoutTree.drawOptions;

  // Track the container's pixel width so the SVG viewBox can expand
  // to fill all available horizontal space.
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
  const baseTreeWidth = baseRectWidth + RECT_TEXT_WIDTH + RECT_X_SPACING;
  const treeHeight = TILE_SIZE_Y * (totalDescendants + 1) + TILE_SIZE_Y_2;

  // The viewBox width is chosen so that when the SVG scales uniformly
  const viewBoxWidth =
    containerWidth > 0 ? Math.max(baseTreeWidth, containerWidth * ZOOM_OUT) : baseTreeWidth;

  // The text-label column stretches to absorb any extra width.
  const effectiveTextWidth = viewBoxWidth - baseRectWidth - RECT_X_SPACING;

  const handleHover = useCallback((id: string | null) => setHoverId(id), []);

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <Box
      ref={containerRef}
      sx={{
        display: "flex",
        flexDirection: "column",
        justifyContent: "flex-start",
        alignItems: "flex-start",
        width: 1,
        flexGrow: 1,
        overflowY: "auto",
      }}
    >
      <Box
        sx={{
          width: 1,
          minWidth: baseTreeWidth / ZOOM_OUT,
          minHeight: treeHeight / ZOOM_OUT,
          display: "flex",
          flexDirection: "column",
          justifyContent: "flex-start",
          alignItems: "flex-start",
        }}
      >
        <svg
          role="img"
          aria-labelledby="variants-tree-title"
          width="100%"
          height={treeHeight / ZOOM_OUT}
          preserveAspectRatio="xMinYMin meet"
          viewBox={`0 0 ${viewBoxWidth} ${treeHeight}`}
        >
          <title id="variants-tree-title">Study variant tree</title>
          <TreeNode
            node={layoutTree}
            depth={0}
            row={0}
            baseRectWidth={baseRectWidth}
            effectiveTextWidth={effectiveTextWidth}
            hoverId={hoverId}
            currentStudyId={study.id}
            isDarkMode={isDarkMode}
            onClick={onClick}
            onHover={handleHover}
          />
        </svg>
      </Box>
    </Box>
  );
}

export default VariantsTree;
