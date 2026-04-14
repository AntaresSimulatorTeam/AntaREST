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

import { Box, CircularProgress, Tooltip, Typography } from "@mui/material";
import { TreeItem, type TreeItemProps } from "@mui/x-tree-view";
import { Children } from "react";

export interface TreeItemEnhancedProps extends TreeItemProps {
  loading?: boolean;
  disableTooltip?: boolean;
}

////////////////////////////////////////////////////////////////
// Utils
////////////////////////////////////////////////////////////////

function withTooltip(label: TreeItemEnhancedProps["label"], disableTooltip: boolean) {
  if (typeof label !== "string") {
    return label;
  }

  const labelEl = (
    <Typography variant="body2" noWrap>
      {label}
    </Typography>
  );

  return disableTooltip ? labelEl : <Tooltip title={label}>{labelEl}</Tooltip>;
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
  label,
  loading = false,
  disableTooltip = false,
  disabled,
  ...rest
}: TreeItemEnhancedProps) {
  const canExpand = Children.toArray(rest.children).length > 0;
  const enhancedLabel = withLoading(withTooltip(label, disableTooltip), loading);

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleClick: NonNullable<TreeItemEnhancedProps["onClick"]> = (event) => {
    event.stopPropagation();

    if (!onClick || disabled) {
      return;
    }

    // Ignore click on the expand/collapse icon.
    if (
      canExpand &&
      event.target instanceof Element &&
      event.target.closest(".MuiTreeItem-iconContainer")
    ) {
      return;
    }

    onClick(event);
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return <TreeItem {...rest} disabled={disabled} onClick={handleClick} label={enhancedLabel} />;
}

export default TreeItemEnhanced;
