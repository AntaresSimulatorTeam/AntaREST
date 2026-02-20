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

import { Box, CircularProgress, type SxProps, type Theme, Tooltip } from "@mui/material";
import { TreeItem, type TreeItemProps } from "@mui/x-tree-view/TreeItem";
import { Children } from "react";
import { mergeSxProp } from "@/utils/muiUtils";

export interface TreeItemEnhancedProps extends TreeItemProps {
  loading?: boolean;
  disableTooltip?: boolean;
}

////////////////////////////////////////////////////////////////
// Utils
////////////////////////////////////////////////////////////////

function getStyles(canExpand: boolean): SxProps<Theme> {
  return {
    "& > .MuiTreeItem-content": {
      p: 0,
      alignItems: "normal",
      // Expand/collapse icon
      "& > .MuiTreeItem-iconContainer": {
        alignItems: "center",
        borderTopLeftRadius: "inherit",
        borderBottomLeftRadius: "inherit",
        "&:hover": {
          background: canExpand ? "inherit" : "none",
        },
      },
      "& > .MuiTreeItem-label": {
        py: 0.5,
        whiteSpace: "nowrap",
        textOverflow: "ellipsis",
        overflow: "hidden",
      },
    },
  };
}

function withTooltip(label: TreeItemEnhancedProps["label"], disableTooltip: boolean) {
  if (disableTooltip || typeof label !== "string") {
    return label;
  }

  return (
    <Tooltip title={label}>
      <span>{label}</span>
    </Tooltip>
  );
}

function withLoading(label: TreeItemEnhancedProps["label"], loading: boolean) {
  if (!loading) {
    return label;
  }

  return (
    <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
      {/* Wrapped with a <Box> to prevent display issue when item is expanded */}
      <Box>
        <CircularProgress size={12} color="secondary" />
      </Box>
      {label}
    </Box>
  );
}

////////////////////////////////////////////////////////////////
// Component
////////////////////////////////////////////////////////////////

function TreeItemEnhanced({
  onClick,
  sx,
  label,
  loading = false,
  disableTooltip = false,
  ...rest
}: TreeItemEnhancedProps) {
  const canExpand = Children.toArray(rest.children).length > 0;
  const enhancedLabel = withLoading(withTooltip(label, disableTooltip), loading);
  const styles = getStyles(canExpand);

  const handleClick: NonNullable<TreeItemEnhancedProps["onClick"]> = (event) => {
    // The item is not selected if the click is on the expand/collapse icon
    if (
      canExpand &&
      event.target instanceof Element &&
      event.target.closest(".MuiTreeItem-iconContainer")
    ) {
      return;
    }

    onClick?.(event);
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <TreeItem {...rest} onClick={handleClick} label={enhancedLabel} sx={mergeSxProp(styles, sx)} />
  );
}

export default TreeItemEnhanced;
