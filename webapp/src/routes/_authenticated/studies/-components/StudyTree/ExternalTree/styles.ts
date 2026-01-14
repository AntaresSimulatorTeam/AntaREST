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

import FolderIcon from "@mui/icons-material/Folder";
import FolderOpenIcon from "@mui/icons-material/FolderOpen";
import StorageIcon from "@mui/icons-material/Storage";
import type { SxProps, Theme } from "@mui/material";

export const treeNodeIcons = {
  workspace: StorageIcon,
  folder: FolderIcon,
  folderOpen: FolderOpenIcon,
};

export const treeItemStyles: SxProps<Theme> = {
  "& > .MuiTreeItem-content": {
    borderRadius: 1,
    px: 1,
    py: 0.25,
    "&:hover": {
      backgroundColor: (theme) => theme.palette.action.hover,
    },
    "&.Mui-selected": {
      backgroundColor: (theme) => theme.palette.action.selected,
      "&:hover": {
        backgroundColor: (theme) => theme.palette.action.hover,
      },
    },
    "&.Mui-focused, &:active": {
      backgroundColor: (theme) => `${theme.palette.info.main}25`,
    },
    "& .MuiTreeItem-iconContainer": {
      mr: 0.5,
      "&:hover": {
        backgroundColor: "transparent",
      },
      "& svg": {
        color: (theme) => theme.palette.text.secondary,
        fontSize: "1.2rem",
        opacity: 0.7,
      },
    },
  },
  "& > .MuiTreeItem-content > .MuiTreeItem-label": {
    fontSize: 14,
    fontWeight: 450,
    color: (theme) => theme.palette.text.secondary,
  },
};

export const workspaceItemStyles: SxProps<Theme> = {
  ...treeItemStyles,
  "& > .MuiTreeItem-content": {
    ...(treeItemStyles["& > .MuiTreeItem-content"] as object),
    "& .MuiTreeItem-iconContainer svg": {
      fontSize: "1.1rem",
      opacity: 0.8,
    },
  },
  "& > .MuiTreeItem-content > .MuiTreeItem-label": {
    fontSize: 14,
    fontWeight: 450,
  },
};
