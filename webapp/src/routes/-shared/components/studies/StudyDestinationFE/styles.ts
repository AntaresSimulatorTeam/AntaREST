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

import { alpha, type SxProps, type Theme } from "@mui/material";

/** Outer flex-column wrapper for the full component. */
export const containerSx: SxProps<Theme> = {
  display: "flex",
  flexDirection: "column",
  width: "100%",
  gap: 1,
};

export const explorerPanelSx = (error: boolean): SxProps<Theme> => ({
  border: "1px solid",
  borderColor: error ? "error.main" : "divider",
  borderRadius: 1,
  overflow: "hidden",
  backgroundColor: (theme) => `${theme.palette.background.paper}30`,
});

/** Toolbar row that houses the go-up button, breadcrumbs, and new directory input. */
export const directoryBreadcrumbsSx: SxProps<Theme> = {
  display: "flex",
  alignItems: "center",
  gap: 0.5,
  px: 0.5,
  minHeight: 40,
  borderBottom: "1px solid",
  borderColor: "divider",
  bgcolor: (theme) => `${theme.palette.info.main}0D`,
};

/**
 * Horizontally scrollable container that holds the breadcrumb buttons and the
 * sub-path input. The scrollbar is intentionally hidden so the bar stays clean.
 */
export const breadcrumbTrackSx: SxProps<Theme> = {
  display: "flex",
  alignItems: "center",
  flex: 1,
  minWidth: 0,
  overflowX: "auto",
  scrollbarWidth: "none",
  "&::-webkit-scrollbar": { display: "none" },
};

/**
 * Clickable ButtonBase for each breadcrumb segment.
 *
 * @param active - Whether this segment is the currently navigated directory.
 * @returns SxProps for the breadcrumb segment ButtonBase.
 */
export const getBreadcrumbSegmentSx = (active: boolean): SxProps<Theme> => ({
  display: "inline-flex",
  alignItems: "center",
  gap: 0.5,
  px: 0.8,
  py: 0.5,
  borderRadius: 0.5,
  fontSize: "0.8rem",
  fontWeight: active ? 600 : 500,
  color: active ? "info.main" : "text.primary",
  flexShrink: 0,
  whiteSpace: "nowrap",
  transition: "background-color 150ms, color 150ms",
  bgcolor: active ? (theme) => alpha(theme.palette.info.main, 0.08) : "transparent",
  "&:hover:not(:disabled)": {
    bgcolor: (theme) => alpha(theme.palette.info.main, active ? 0.16 : 0.06),
  },
});

export const getNewDirectoryInputSx = (hasText: boolean): SxProps<Theme> => ({
  flex: 1,
  minWidth: 100,
  "& .MuiInputBase-input": {
    p: 0.5,
    fontSize: "0.8rem",
    color: hasText ? "inherit" : "text.disabled",
    fontStyle: hasText ? "normal" : "italic",
    fontWeight: hasText ? 500 : 400,
  },
});

/** The scrollable list that shows the direct children of the current directory. */
export const directoryListSx: SxProps<Theme> = {
  m: 0,
  p: 0,
  listStyle: "none",
  minHeight: 500,
  overflowY: "auto",
  bgcolor: "background.paper",
};

/** Centred placeholder shown when the current directory has no sub-directories. */
export const emptyStateSx: SxProps<Theme> = {
  display: "flex",
  alignItems: "center",
  justifyContent: "center",
  height: "100%",
};

export const getDirectoryRowSx: SxProps<Theme> = {
  display: "flex",
  alignItems: "center",
  gap: 1,
  px: 2,
  py: 1,
  cursor: "pointer",
  userSelect: "none",
  transition: "background-color 100ms",
  // Zebra striping lives on the row so hover/active always take precedence
  "&:nth-of-type(even)": {
    bgcolor: (theme) => alpha(theme.palette.info.main, 0.04),
  },
  "&:hover": {
    bgcolor: (theme) => alpha(theme.palette.info.main, 0.12),
  },
  "&:focus-visible": {
    outline: "none",
  },
  "&:active": {
    bgcolor: (theme) => alpha(theme.palette.info.main, 0.2),
  },
};
