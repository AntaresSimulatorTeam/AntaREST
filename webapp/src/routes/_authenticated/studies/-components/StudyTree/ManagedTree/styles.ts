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

export const editableRowStyles: SxProps<Theme> = {
  display: "flex",
  alignItems: "center",
  gap: 0.5,
  borderRadius: 1,
  px: 1,
  py: 0.25,
  backgroundColor: (theme) => `${theme.palette.info.main}08`,
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

export const nodeLabelContainerStyles: SxProps<Theme> = {
  display: "flex",
  alignItems: "center",
  justifyContent: "space-between",
  width: "100%",
  pr: 0.5,
};

export const nodeActionsContainerStyles: SxProps<Theme> = {
  display: "flex",
  gap: 0.25,
  ml: 1,
};

export const actionButtonStyles: SxProps<Theme> = {
  p: 0.25,
  opacity: 0,
  ".MuiTreeItem-content:hover &": {
    opacity: 1,
  },
};

export const renameIconStyles: SxProps<Theme> = {
  fontSize: 16,
};

export const addSubDirectoryIconStyles: SxProps<Theme> = {
  fontSize: 16,
};

export const deleteIconStyles: SxProps<Theme> = {
  fontSize: 16,
  color: "error.main",
};
