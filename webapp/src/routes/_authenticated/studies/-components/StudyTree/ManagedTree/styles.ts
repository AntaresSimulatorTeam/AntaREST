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
import type { SxProps, Theme } from "@mui/material";

export const treeNodeIcons = {
  folder: FolderIcon,
  folderOpen: FolderOpenIcon,
};

export const treeItemStyles: SxProps<Theme> = {
  "& > .MuiTreeItem-content": {
    borderRadius: 1,
    px: 1,
    py: 0.25,
    "&:hover": {
      backgroundColor: (theme) => `${theme.palette.info.main}10`,
    },
    "&.Mui-selected": {
      backgroundColor: (theme) => `${theme.palette.info.main}20`,
      "&:hover": {
        backgroundColor: (theme) => `${theme.palette.info.main}30`,
      },
    },
    "&.Mui-selected.Mui-focused": {
      backgroundColor: (theme) => `${theme.palette.info.main}25`,
    },

    "& .MuiTreeItem-iconContainer": {
      mr: 0.5,
      "&:hover": {
        backgroundColor: "transparent",
      },
      "& svg": {
        color: (theme) => theme.palette.info.main,
        fontSize: "1.2rem",
      },
    },
  },
  "& > .MuiTreeItem-content > .MuiTreeItem-label": {
    fontSize: 14,
    fontWeight: 450,
  },
};

export const editableTreeItemStyles: SxProps<Theme> = {
  ...treeItemStyles,
  "& > .MuiTreeItem-content": {
    ...(treeItemStyles["& > .MuiTreeItem-content"] as object),
    backgroundColor: (theme) => `${theme.palette.info.main}08`,
    "&:hover": {
      backgroundColor: (theme) => `${theme.palette.info.main}12`,
    },
  },
};

export const textFieldStyles: SxProps<Theme> = {
  width: "auto",
  maxWidth: "250px",
  "& .MuiInputBase-root": {
    backgroundColor: "background.paper",
  },
  "& .MuiInputBase-input": {
    py: 0.25,
    px: 1,
    fontSize: 14,
    fontWeight: 450,
    color: "text.primary",
  },
  "& .MuiOutlinedInput-notchedOutline": {
    borderColor: "info.main",
    borderWidth: 1,
  },
  "& .MuiOutlinedInput-root:hover .MuiOutlinedInput-notchedOutline": {
    borderColor: "info.main",
  },
  "& .MuiOutlinedInput-root.Mui-focused .MuiOutlinedInput-notchedOutline": {
    borderColor: "info.main",
    borderWidth: 2,
  },
};
