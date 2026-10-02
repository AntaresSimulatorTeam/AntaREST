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
import type { TFunction } from "i18next";
import { withOpacity } from "@/utils/muiUtils";

export type TreeVariant = "managed" | "external";

export function variantColor(variant: TreeVariant) {
  return variant === "managed" ? "info.main" : "text.secondary";
}

export function variantLabel(variant: TreeVariant, t: TFunction): string {
  return t(variant === "managed" ? "studies.tree.managed.short" : "studies.tree.external.short");
}

export function separatorSx(variant: TreeVariant): SxProps<Theme> {
  return {
    "& .MuiBreadcrumbs-separator": {
      color: variantColor(variant),
      opacity: 0.55,
      transition: "color 200ms ease, opacity 200ms ease",
    },
  };
}

export function chipSx(variant: TreeVariant, interactive: boolean) {
  return (theme: Theme) => {
    const color =
      variant === "managed" ? theme.vars.palette.info.main : theme.vars.palette.text.secondary;

    return {
      display: "inline-flex",
      alignItems: "center",
      gap: 0.5,
      px: 0.75,
      py: 0.125,
      bgcolor: withOpacity(color, 0.12),
      border: 0,
      borderLeft: `3px solid ${color}`,
      borderRadius: "1px 4px 4px 1px",
      color: "text.primary",
      font: "inherit",
      lineHeight: 1.6,
      textDecoration: "none",
      cursor: interactive ? "pointer" : "default",
      flexShrink: 0,
      transition: "background-color 200ms ease, transform 150ms ease",
      ...(interactive && {
        "&:hover": { bgcolor: withOpacity(color, 0.18) },
        "&:active": { transform: "scale(0.97)" },
        "&:focus-visible": {
          outline: `2px solid ${withOpacity(color, 0.6)}`,
          outlineOffset: 1,
        },
      }),
    };
  };
}
