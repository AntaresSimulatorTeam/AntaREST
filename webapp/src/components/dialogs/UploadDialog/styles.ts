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

const uploadPanelSx = {
  minHeight: 192,
  p: { xs: 2, sm: 3 },
  border: 1,
  borderColor: "divider",
} satisfies SxProps<Theme>;

export const uploadProgressSx = {
  ...uploadPanelSx,
  borderRadius: 1,
  bgcolor: "action.hover",
} satisfies SxProps<Theme>;

export const dropzoneSx = {
  ...uploadPanelSx,
  borderStyle: "dashed",
  cursor: "pointer",
  textAlign: "center",
  bgcolor: "transparent",
  "&:hover": {
    borderColor: "primary.main",
    bgcolor: "action.hover",
  },
  "&:focus-visible": {
    outline: "2px solid",
    outlineColor: "primary.main",
    outlineOffset: 3,
  },
} satisfies SxProps<Theme>;
