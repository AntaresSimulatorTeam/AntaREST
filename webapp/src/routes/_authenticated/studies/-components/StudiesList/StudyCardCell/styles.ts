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

import type { StudyMetadata } from "@/types/types";
import type { SxProps, Theme } from "@mui/material";

export const chipSx = {
  height: 20,
  "& .MuiChip-label": { px: 0.75, fontSize: "0.7rem" },
} satisfies SxProps<Theme>;

export const variantChipSx = {
  ...chipSx,
  flexShrink: 0,
  "& .MuiChip-icon": { fontSize: "0.8rem", ml: 0.5 },
} satisfies SxProps<Theme>;

// Returns MUI color tokens for the study title and accent border,
// derived from study state. Used consistently in both Grid and List layouts.
export function getStudyColors(study: Pick<StudyMetadata, "managed" | "archived">): {
  titleColor: string;
  accentColor: string;
} {
  if (study.archived) {
    return { titleColor: "warning.main", accentColor: "warning.main" };
  }

  if (study.managed) {
    return { titleColor: "info.main", accentColor: "info.main" };
  }

  // Disk studies
  return { titleColor: "text.secondary", accentColor: "action.disabled" };
}

// Base Card sx shared by both GridStudyCard and ListStudyCard.
// Handles width/height, left accent border, and selection outline.
export function cardSx(
  width: number,
  height: number,
  accentColor: string,
  isSelected: boolean,
): SxProps<Theme> {
  return {
    width,
    height,
    display: "flex",
    flexDirection: "column",
    position: "relative",
    borderLeft: "3px solid",
    borderLeftColor: accentColor,
    outline: isSelected ? "1.5px solid" : "none",
    outlineColor: "primary.main",
  };
}

// Layout base shared by both grid and list CardContent wrappers.
export const cardContentBaseSx = {
  flexGrow: 1,
  display: "flex",
  flexDirection: "column",
  justifyContent: "center",
  overflow: "hidden",
} satisfies SxProps<Theme>;

// Grid-specific CardContent padding.
export const gridCardContentSx = {
  px: 1.5,
  py: 1,
  "&:last-child": { pb: 1 },
} satisfies SxProps<Theme>;

// List-specific CardContent padding (compact).
export const listCardContentSx = {
  px: 1.5,
  py: 0.75,
  "&:last-child": { pb: 0.75 },
} satisfies SxProps<Theme>;

export const studyTitleBaseSx = {
  flex: 1,
  cursor: "pointer",
  textDecoration: "underline",
  textDecorationColor: "transparent",
  "&:hover": { textDecorationColor: "currentColor" },
} satisfies SxProps<Theme>;

// Shared flex row for aligning icon + text horizontally with overflow clipping.
export const rowSx = {
  display: "flex",
  alignItems: "center",
  gap: 0.5,
  overflow: "hidden",
} satisfies SxProps<Theme>;

// Flex child that fills available space and clips overflowing text.
export const overflowBoxSx = {
  flex: 1,
  display: "flex",
  alignItems: "center",
  gap: 0.5,
  overflow: "hidden",
  minWidth: 0,
} satisfies SxProps<Theme>;

export const studyTypeIconSx = {
  fontSize: 16,
  flexShrink: 0,
} satisfies SxProps<Theme>;

export const directoryLinkIconSx = {
  flexShrink: 0,
  color: "inherit",
} satisfies SxProps<Theme>;

export const directoryLinkTextSx = {
  cursor: "pointer",
  overflow: "hidden",
  textOverflow: "ellipsis",
  whiteSpace: "nowrap",
  minWidth: 0,
} satisfies SxProps<Theme>;
