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

import { Box, CircularProgress, Tooltip } from "@mui/material";
import { TreeItem, type TreeItemProps } from "@mui/x-tree-view/TreeItem";
import * as R from "ramda";
import { mergeSxProp } from "../../utils/muiUtils";

export interface TreeItemEnhancedProps extends TreeItemProps {
  loading?: boolean;
}

function TreeItemEnhanced({
  onClick,
  sx,
  label: labelFromProps,
  loading,
  ...rest
}: TreeItemEnhancedProps) {
  const canExpand = rest.children && R.isNotEmpty(rest.children);

  ////////////////////////////////////////////////////////////////
  // Label
  ////////////////////////////////////////////////////////////////

  const addLabelTooltip = (label: TreeItemEnhancedProps["label"]) => {
    return typeof label === "string" ? (
      <Tooltip title={label}>
        <span>{label}</span>
      </Tooltip>
    ) : (
      label
    );
  };

  const addLabelLoading = (label: TreeItemEnhancedProps["label"]) => {
    return loading ? (
      <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
        {/* Wrapped with a <Box> to prevent display issue when item is expanded */}
        <Box>
          <CircularProgress size={12} color="secondary" />
        </Box>
        {label}
      </Box>
    ) : (
      label
    );
  };

  const enhanceLabel = R.compose(addLabelLoading, addLabelTooltip);

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleClick: TreeItemEnhancedProps["onClick"] = (event) => {
    const { target } = event;

    // The item is not selected if the click is on the expand/collapse icon
    if (canExpand && target instanceof Element && target.closest(".MuiTreeItem-iconContainer")) {
      return;
    }

    onClick?.(event);
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <TreeItem
      {...rest}
      onClick={handleClick}
      label={enhanceLabel(labelFromProps)}
      sx={mergeSxProp(
        {
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
        },
        sx,
      )}
    />
  );
}

export default TreeItemEnhanced;
