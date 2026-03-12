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

import { withOpacity } from "@/utils/muiUtils";
import type { SxProps, Theme } from "@mui/material";
import type { TreeSectionVariant } from "./TreeSection";

export const ICON_SIZE = 18;
export const ICON_BUTTON_PADDING = 0.5;

////////////////////////////////////////////////////////////////
// Shared styles
////////////////////////////////////////////////////////////////

export const titleStyles = {
  fontWeight: 600,
  textTransform: "uppercase",
  letterSpacing: 0.5,
} satisfies SxProps<Theme>;

const containerBaseStyles = {
  borderLeftWidth: 3,
  borderLeftStyle: "solid",
  p: 0.5,
  display: "flex",
  flexDirection: "column",
  minHeight: 0,
} satisfies SxProps<Theme>;

////////////////////////////////////////////////////////////////
// Variant styles
////////////////////////////////////////////////////////////////

export const variantStyles = {
  managed: {
    container: (theme: Theme) => ({
      ...containerBaseStyles,
      backgroundColor: withOpacity(theme.vars.palette.info.main, 0.05),
      borderLeftColor: theme.vars.palette.info.main,
    }),
    iconColor: "info.main" as const,
    titleColor: "info.main" as const,
  },
  external: {
    container: (theme: Theme) => ({
      ...containerBaseStyles,
      backgroundColor: withOpacity(theme.vars.palette.action.disabled, 0.2),
      borderLeftColor: theme.vars.palette.action.disabled,
    }),
    iconColor: "text.secondary" as const,
    titleColor: "text.secondary" as const,
  },
} satisfies Record<
  TreeSectionVariant,
  {
    container: (theme: Theme) => SxProps<Theme>;
    iconColor: string;
    titleColor: string;
  }
>;

////////////////////////////////////////////////////////////////
// Component styles
////////////////////////////////////////////////////////////////

// Content row: no padding (inner wrapper handles it), clips during collapse animation
export const contentSxOverride = { p: 0, overflow: "hidden" } satisfies SxProps<Theme>;

export const innerContentSx = {
  flex: 1,
  minHeight: 0,
} satisfies SxProps<Theme>;

export const scrollbarStyle = { height: "100%" };

export const studyTreeGridSx = (gridTemplateRows: string): SxProps<Theme> => ({
  height: 1,
  display: "grid",
  gridTemplateRows,
  alignContent: "start",
  transition: "grid-template-rows 250ms ease",
  overflow: "hidden",
});
