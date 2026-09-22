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

import type { SxProps, Theme } from "@mui/material";
import { withOpacity } from "@/utils/muiUtils";

/**
 * Outer flex-column wrapper for the full component.
 *
 * @param fillHeight - When true, the wrapper grows to fill its flex parent
 *   (used by dialogs that want the explorer to take the remaining vertical space).
 * @returns SxProps for the outer wrapper.
 */
export const getContainerSx = (fillHeight: boolean): SxProps<Theme> => ({
  display: "flex",
  flexDirection: "column",
  width: "100%",
  gap: 1,
  ...(fillHeight && { flex: 1, minHeight: 0 }),
});

/**
 * Builds the bordered explorer panel styles.
 *
 * @param error - Whether the field is in an error state.
 * @param fillHeight - When true, the panel becomes a flex column that grows to fill its parent.
 * @returns SxProps for the explorer panel.
 */
export const getExplorerPanelSx = (error: boolean, fillHeight: boolean): SxProps<Theme> => ({
  border: "1px solid",
  borderColor: error ? "error.main" : "divider",
  borderRadius: 1,
  overflow: "hidden",
  backgroundColor: (theme) => withOpacity(theme.vars.palette.background.paper, 0.19),
  ...(fillHeight && { flex: 1, minHeight: 0, display: "flex", flexDirection: "column" }),
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
  bgcolor: (theme) => withOpacity(theme.vars.palette.info.main, 0.05),
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
  bgcolor: active ? (theme) => withOpacity(theme.vars.palette.info.main, 0.08) : "transparent",
  "&:hover:not(:disabled)": {
    bgcolor: (theme) => withOpacity(theme.vars.palette.info.main, active ? 0.16 : 0.06),
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

/**
 * Builds the scrollable directory list styles.
 *
 * @param listHeight - When provided, locks the list to a fixed height.
 * @param fillHeight - When true, the list flex-grows to fill its parent (overrides `listHeight`).
 *   When both are falsy, the list grows between 400 and 700px (default for full-page dialogs).
 * @returns SxProps for the directory list.
 */
export const getDirectoryListSx = (
  listHeight: number | string | undefined,
  fillHeight: boolean,
): SxProps<Theme> => ({
  m: 0,
  p: 0,
  listStyle: "none",
  display: "flex",
  flexDirection: "column",
  ...(fillHeight
    ? { flex: 1, minHeight: 0 }
    : listHeight !== undefined
      ? { height: listHeight }
      : { minHeight: 400, maxHeight: 700 }),
  overflowY: "auto",
  bgcolor: "background.paper",
});

/** Centred placeholder shown when the current directory has no sub-directories. */
export const emptyStateSx: SxProps<Theme> = {
  display: "flex",
  alignItems: "center",
  justifyContent: "center",
  flex: 1,
};

export const getDirectoryRowSx: SxProps<Theme> = {
  display: "flex",
  alignItems: "center",
  gap: 1,
  px: 2,
  py: 1,
  cursor: "pointer",
  userSelect: "none",
  transition: "background-color 200ms",
  "&:hover": {
    bgcolor: (theme) => withOpacity(theme.vars.palette.info.main, 0.12),
  },
  "&:focus-visible": {
    outline: "none",
  },
  "&:active": {
    bgcolor: (theme) => withOpacity(theme.vars.palette.info.main, 0.2),
  },
};
