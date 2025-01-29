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

import { TreeItem, type TreeItemProps } from "@mui/x-tree-view/TreeItem";
import { mergeSxProp } from "../../utils/muiUtils";
import * as R from "ramda";
import { Tooltip } from "@mui/material";

export type TreeItemEnhancedProps = TreeItemProps;

function TreeItemEnhanced({ onClick, sx, label, ...rest }: TreeItemEnhancedProps) {
  const canExpand = rest.children && R.isNotEmpty(rest.children);

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
      label={
        typeof label === "string" ? (
          <Tooltip title={label}>
            <span>{label}</span>
          </Tooltip>
        ) : (
          label
        )
      }
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
