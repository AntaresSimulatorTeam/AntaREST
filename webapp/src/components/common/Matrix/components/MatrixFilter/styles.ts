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

import type { SxProps, Theme } from "@mui/material";

// Design tokens for consistent spacing and sizing
export const DESIGN_TOKENS = {
  spacing: {
    xs: 0.25,
    sm: 0.5,
    md: 0.75,
    lg: 1,
    xl: 1.5,
  },
  fontSize: {
    xs: "0.6rem",
    sm: "0.65rem",
    md: "0.8rem",
    lg: "1rem",
  },
  borderRadius: {
    sm: "3px",
  },
  zIndex: {
    drawer: 1300,
  },
} as const;

// Component-specific dimensions and measurements
export const COMPONENT_DIMENSIONS = {
  drawer: {
    width: 380,
    maxWidth: 380,
    transitionDuration: 200,
  },
  chip: {
    height: 18,
  },
  scrollbar: {
    width: "6px",
  },
} as const;

// Color palette for component styling
export const COMPONENT_COLORS = {
  scrollbar: {
    thumb: "rgba(0,0,0,0.2)",
    thumbHover: "rgba(0,0,0,0.3)",
  },
  preview: {
    border: "rgba(33, 150, 243, 0.3)",
    shadow: "rgba(33, 150, 243, 0.2)",
  },
} as const;

// Drawer component styles
export const DRAWER_STYLES = {
  paper: {
    p: DESIGN_TOKENS.spacing.xl,
    width: `${COMPONENT_DIMENSIONS.drawer.width}px`,
    maxWidth: `${COMPONENT_DIMENSIONS.drawer.maxWidth}px`,
    display: "flex",
    flexDirection: "column" as const,
    height: "100vh",
  },
  scrollableContent: {
    flex: 1,
    overflowY: "overlay" as const,
    overflowX: "hidden" as const,
    minHeight: 0,
    pr: DESIGN_TOKENS.spacing.sm,
    "&::-webkit-scrollbar": {
      width: COMPONENT_DIMENSIONS.scrollbar.width,
    },
    "&::-webkit-scrollbar-track": {
      background: "transparent",
    },
    "&::-webkit-scrollbar-thumb": {
      background: COMPONENT_COLORS.scrollbar.thumb,
      borderRadius: DESIGN_TOKENS.borderRadius.sm,
      "&:hover": {
        background: COMPONENT_COLORS.scrollbar.thumbHover,
      },
    },
    scrollbarWidth: "thin" as const,
    scrollbarColor: `${COMPONENT_COLORS.scrollbar.thumb} transparent`,
  },
} as const satisfies Record<string, SxProps<Theme>>;

// Chip component styles
export const CHIP_STYLES = {
  base: {
    height: COMPONENT_DIMENSIONS.chip.height,
    fontSize: DESIGN_TOKENS.fontSize.xs,
    "& .MuiChip-label": {
      px: DESIGN_TOKENS.spacing.sm,
    },
  },
  preview: {
    borderColor: "info.main",
    color: "info.main",
  },
} as const satisfies Record<string, SxProps<Theme>>;

// Button component styles
export const BUTTON_STYLES = {
  base: {
    fontSize: DESIGN_TOKENS.fontSize.md,
    py: DESIGN_TOKENS.spacing.sm,
  },
  compact: {
    fontSize: DESIGN_TOKENS.fontSize.xs,
    py: DESIGN_TOKENS.spacing.sm,
    px: DESIGN_TOKENS.spacing.lg,
    minHeight: 28,
    height: 28,
  },
  compactIconOnly: {
    fontSize: DESIGN_TOKENS.fontSize.xs,
    py: DESIGN_TOKENS.spacing.sm,
    px: DESIGN_TOKENS.spacing.sm,
    minHeight: 28,
    height: 28,
    minWidth: 28,
    width: 28,
  },
} as const satisfies Record<string, SxProps<Theme>>;

// Typography styles
export const TYPOGRAPHY_STYLES = {
  title: {
    fontSize: DESIGN_TOKENS.fontSize.lg,
  },
  caption: {
    fontSize: DESIGN_TOKENS.fontSize.sm,
  },
  sectionTitle: {
    fontSize: DESIGN_TOKENS.fontSize.md,
    fontWeight: 500,
  },
  smallCaption: {
    fontSize: DESIGN_TOKENS.fontSize.xs,
  },
  valueDisplay: {
    fontSize: DESIGN_TOKENS.fontSize.md,
  },
} as const satisfies Record<string, SxProps<Theme>>;

// Layout spacing utilities
export const LAYOUT_SPACING = {
  section: {
    marginBottom: DESIGN_TOKENS.spacing.lg,
    flexShrink: 0,
  },
  content: {
    marginTop: DESIGN_TOKENS.spacing.sm,
  },
} as const satisfies Record<string, SxProps<Theme>>;

// Form component styles
export const FORM_STYLES = {
  formControl: {
    fontSize: DESIGN_TOKENS.fontSize.md,
    "& .MuiInputLabel-root": {
      fontSize: DESIGN_TOKENS.fontSize.md,
      overflow: "hidden",
      textOverflow: "ellipsis",
      whiteSpace: "nowrap",
      maxWidth: "calc(100% - 24px)", // Account for shrink animation
    },
    "& .MuiSelect-select": {
      fontSize: DESIGN_TOKENS.fontSize.md,
    },
    "& .MuiInputBase-input": {
      fontSize: DESIGN_TOKENS.fontSize.md,
    },
  },
  menuItem: {
    fontSize: DESIGN_TOKENS.fontSize.md,
  },
  textField: {
    "& .MuiInputBase-input": {
      fontSize: DESIGN_TOKENS.fontSize.md,
    },
    "& .MuiInputLabel-root": {
      fontSize: DESIGN_TOKENS.fontSize.md,
      overflow: "hidden",
      textOverflow: "ellipsis",
      whiteSpace: "nowrap",
      maxWidth: "calc(100% - 24px)", // Account for shrink animation
    },
    "& .MuiFormHelperText-root": {
      fontSize: DESIGN_TOKENS.fontSize.xs,
    },
  },
  sideBySideContainer: {
    display: "flex",
    gap: DESIGN_TOKENS.spacing.lg,
    mb: DESIGN_TOKENS.spacing.lg,
    flexDirection: "row" as const,
    "& > *": {
      flex: 1,
      minWidth: 0, // Prevent flex items from overflowing
    },
    "@media (max-width: 480px)": {
      flexDirection: "column" as const,
      gap: DESIGN_TOKENS.spacing.md,
    },
  },
  responsiveContainer: {
    display: "flex",
    gap: DESIGN_TOKENS.spacing.lg,
    mb: DESIGN_TOKENS.spacing.lg,
    flexDirection: "row" as const,
    alignItems: "flex-start",
    "@media (max-width: 360px)": {
      flexDirection: "column" as const,
      gap: DESIGN_TOKENS.spacing.md,
    },
  },
  sideBySideFormControl: {
    fontSize: DESIGN_TOKENS.fontSize.md,
    "& .MuiInputLabel-root": {
      fontSize: DESIGN_TOKENS.fontSize.md,
      overflow: "hidden",
      textOverflow: "ellipsis",
      whiteSpace: "nowrap",
      maxWidth: "calc(100% - 32px)", // Account for shrink animation and padding
      "&.MuiInputLabel-shrink": {
        maxWidth: "calc(133% - 32px)", // Allow more space when shrunk
        transform: "translate(14px, -9px) scale(0.75)",
      },
    },
    "& .MuiSelect-select": {
      fontSize: DESIGN_TOKENS.fontSize.md,
    },
    "& .MuiInputBase-input": {
      fontSize: DESIGN_TOKENS.fontSize.md,
    },
    "& .MuiOutlinedInput-notchedOutline": {
      "& legend": {
        maxWidth: "100%",
        "& span": {
          overflow: "hidden",
          textOverflow: "ellipsis",
          whiteSpace: "nowrap",
        },
      },
    },
  },
} as const satisfies Record<string, SxProps<Theme>>;

// Accordion component styles
export const ACCORDION_STYLES = {
  summary: {
    py: 0,
    my: 0,
    maxHeight: 35,
    minHeight: 0,
  },
  details: {
    pt: DESIGN_TOKENS.spacing.sm,
    pb: DESIGN_TOKENS.spacing.lg,
  },
  marginBottom: {
    mb: DESIGN_TOKENS.spacing.lg,
  },
} as const satisfies Record<string, SxProps<Theme>>;

// Icon button styles
export const ICON_BUTTON_STYLES = {
  small: {
    p: DESIGN_TOKENS.spacing.sm,
  },
  extraSmall: {
    p: DESIGN_TOKENS.spacing.xs,
  },
} as const satisfies Record<string, SxProps<Theme>>;

// Common container styles
export const CONTAINER_STYLES = {
  flexRow: {
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    width: "100%",
  },
  flexRowGap: {
    display: "flex",
    gap: DESIGN_TOKENS.spacing.lg,
  },
  centeredFlex: {
    display: "flex",
    justifyContent: "center",
    alignItems: "center",
  },
  section: {
    mb: DESIGN_TOKENS.spacing.lg,
  },
} as const satisfies Record<string, SxProps<Theme>>;

// Chip selector styles
export const CHIP_SELECTOR_STYLES = {
  dense: {
    m: 0.125,
    minWidth: 28,
    height: 18,
    fontSize: DESIGN_TOKENS.fontSize.xs,
    "& .MuiChip-label": {
      px: DESIGN_TOKENS.spacing.sm,
    },
  },
  normal: {
    my: DESIGN_TOKENS.spacing.xs,
    height: 24,
    fontSize: DESIGN_TOKENS.fontSize.md,
    "& .MuiChip-label": {
      px: DESIGN_TOKENS.spacing.md,
    },
  },
} as const satisfies Record<string, SxProps<Theme>>;

// Selection summary styles
export const SELECTION_SUMMARY_STYLES = {
  container: {
    p: DESIGN_TOKENS.spacing.sm,
  },
  statsContainer: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
  },
  statItem: {
    textAlign: "center" as const,
    flex: 1,
  },
  label: {
    fontSize: DESIGN_TOKENS.fontSize.sm,
  },
  value: {
    display: "block",
    fontSize: DESIGN_TOKENS.fontSize.md,
  },
} as const satisfies Record<string, SxProps<Theme>>;

// Operation styles
export const OPERATION_STYLES = {
  submitButton: {
    fontSize: DESIGN_TOKENS.fontSize.xs,
    py: DESIGN_TOKENS.spacing.sm,
  },
  container: {
    mt: DESIGN_TOKENS.spacing.lg,
    display: "flex",
    justifyContent: "flex-end",
  },
} as const satisfies Record<string, SxProps<Theme>>;

// Preview mode styles
export const PREVIEW_STYLES = {
  container: {
    boxShadow: `0 0 0 1px ${COMPONENT_COLORS.preview.shadow}`,
    borderColor: COMPONENT_COLORS.preview.border,
  },
} as const satisfies Record<string, SxProps<Theme>>;
