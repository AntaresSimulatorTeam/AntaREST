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

export const indicatorStyles = {
  display: "flex",
  alignItems: "center",
  gap: 0.5,
  height: 20,
  width: 80,
  flexShrink: 0,
  minWidth: 0,
  color: "text.secondary",
  borderRadius: 0.5,
  "&:focus-visible": {
    outline: "2px solid",
    outlineColor: "primary.main",
    outlineOffset: 1,
  },
} satisfies SxProps<Theme>;

export const progressStyles = {
  flex: 1,
  height: 4,
  borderRadius: 1,
  backgroundColor: "action.disabledBackground",
  "& .MuiLinearProgress-bar": { borderRadius: 1 },
} satisfies SxProps<Theme>;

export const percentageStyles = {
  width: "5ch",
  flexShrink: 0,
  whiteSpace: "nowrap",
  textAlign: "right",
  fontVariantNumeric: "tabular-nums",
  lineHeight: 1,
} satisfies SxProps<Theme>;
