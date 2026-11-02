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

import { formControlLabelClasses, type SxProps, type Theme } from "@mui/material";

/** Compact dialog height with consistent action spacing, capped to the viewport by MUI. */
export const studyDestinationDialogPaperSx = {
  height: 640,
  ".MuiDialogActions-root": { px: 3, pt: 1.5, pb: 2 },
} satisfies SxProps<Theme>;

/** Keeps destination forms bounded so their fields and explorer can scroll independently. */
export const studyDestinationDialogContentSx: SxProps<Theme> = {
  overflow: "hidden",
  ".Form": { overflow: "hidden", minHeight: 0 },
  ".Form .Form__Content": {
    display: "flex",
    flexDirection: "column",
    overflow: "hidden",
    minHeight: 0,
    flex: 1,
    p: 0,
  },
};

/** Keeps the completion preference readable, including when its label wraps. */
export const studyDestinationRedirectSx = {
  width: 1,
  flexShrink: 0,
  px: 1,
  py: 0.5,
  borderRadius: 1,
  bgcolor: "action.hover",
  [`& .${formControlLabelClasses.root}`]: { m: 0, alignItems: "flex-start" },
  [`& .${formControlLabelClasses.label}`]: { typography: "body2", py: 1 },
} satisfies SxProps<Theme>;
